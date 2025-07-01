# app_nhatro_baocao.py
import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- HÀM HỖ TRỢ ---
def parse_value(column_name, value):
    column_name = column_name.upper()
    if "THANG" in column_name:
        try:
            return datetime.strptime(str(value), "%Y-%m").strftime("%Y-%m")
        except:
            return ""
    elif "NGAY" in column_name:
        try:
            return pd.to_datetime(value).strftime("%Y-%m-%d")
        except:
            return ""
    elif any(x in column_name for x in ["TIEN", "SO_TIEN"]):
        try:
            return float(str(value).replace(",", "").replace(".", ""))
        except:
            return 0.0
    elif "CHI_SO" in column_name:
        try:
            return int(value)
        except:
            return 0
    elif column_name == "DA_THANH_TOAN":
        return str(value).strip().lower() in ["co", "yes", "true", "1", "da thanh toan"]
    else:
        return str(value).strip()

# --- CẤU HÌNH ---
ZIP_FILE = "secret_key.zip"
st.set_page_config(page_title="Báo cáo nhà trọ", layout="centered")
st.title("\U0001F4C8 Báo cáo tổng hợp thu chi nhà trọ")

# --- NHẬP MẬT KHẨU ZIP ---
pwd = st.text_input("\U0001F510 Nhập mật khẩu file ZIP:", type="password")
if not pwd:
    st.stop()

# --- GIẢI NÉN & KẾT NỐI GOOGLE SHEET ---
with tempfile.TemporaryDirectory() as tmpdir:
    try:
        with pyzipper.AESZipFile(ZIP_FILE, 'r') as z:
            z.pwd = pwd.encode()
            z.extractall(tmpdir)
        json_file = next((f for f in os.listdir(tmpdir) if f.endswith(".json")), None)
        if not json_file:
            st.error("❌ Không tìm thấy file .json.")
            st.stop()

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            os.path.join(tmpdir, json_file),
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        st.success("✅ Kết nối thành công!")

        sheet_url = st.text_input("\U0001F517 Dán link Google Sheet tại đây:")
        if not sheet_url:
            st.stop()

        sheet = client.open_by_url(sheet_url).sheet1
        df = pd.DataFrame(sheet.get_all_records(empty2zero=False, default_blank=""))
        df = df.loc[:, df.columns.notnull()].dropna(axis=1, how='all')

        if df.empty:
            st.warning("Sheet chưa có dữ liệu.")
            st.stop()

        df.columns = [col.strip().upper().replace(" ", "_") for col in df.columns]
        df['THANG_PARSED'] = pd.to_datetime(df['THANG'], format="%d/%m/%Y", errors='coerce')
        df['THANG_STR'] = df['THANG_PARSED'].dt.strftime("%m/%Y")

        # --- CHUYỂN ĐỔI CỘT SỐ ---
        num_cols = [c for c in df.columns if any(x in c for x in ["TIEN", "SO_TIEN", "TONG_CONG", "CHI_SO", "SO_DIEN", "SO_NUOC"])]
        for col in num_cols:
            try:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "").str.replace(".", ""), errors="coerce").fillna(0)
            except Exception as e:
                st.error(f"❌ Lỗi chuyển cột {col}: {e}")

        # --- BÁO CÁO ---
        st.header("\U0001F4CB Tổng hợp doanh thu")
        thang_selected = st.selectbox("Chọn tháng:", options=sorted(df['THANG_STR'].dropna().unique(), reverse=True))
        df_thang = df[df['THANG_STR'] == thang_selected]

        try:
            total_thu = df_thang['TONG_CONG'].sum()
            so_phong = df_thang['SO_PHONG'].nunique()
            da_thu = df_thang[df_thang['DA_THANH_TOAN'] == True]['TONG_CONG'].sum()
            chua_thu = total_thu - da_thu
        except Exception as e:
            st.error(f"❌ Lỗi tính toán doanh thu: {e}")
            total_thu = da_thu = chua_thu = 0
            so_phong = 0

        col1, col2, col3 = st.columns(3)
        col1.metric("\U0001F4B0 Tổng thu", f"{total_thu:,.0f} đ")
        col2.metric("\U0001F3E0 Số phòng", so_phong)
        col3.metric("\u274C Chưa thu", f"{chua_thu:,.0f} đ")

        st.divider()

        st.subheader("\U0001F4CA Chi tiết theo phòng")
        df_display = df_thang[["SO_PHONG", "HO_TEN_KHACH_THUE", "TONG_CONG", "DA_THANH_TOAN"]].copy()
        df_display['TONG_CONG'] = df_display['TONG_CONG'].apply(lambda x: f"{x:,.0f} đ")
        df_display['DA_THANH_TOAN'] = df_display['DA_THANH_TOAN'].apply(lambda x: "✅" if str(x).lower() in ['co', 'yes', 'true', '1', 'da thanh toan'] else "❌")
        st.dataframe(df_display, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Lỗi hệ thống: {e}")
