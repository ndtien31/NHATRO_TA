# app_nhatro_google_sheet.py
import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def colnum_to_excel_col(n):
    name = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        name = chr(65 + r) + name
    return name

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
            return float(value)
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

def format_value(k, v):
    k = k.upper()
    if "THANG" in k:
        try:
            return pd.to_datetime(v).strftime('%Y-%m')
        except: return v
    if "NGAY" in k:
        try:
            return pd.to_datetime(v).strftime('%Y-%m-%d')
        except: return v
    return v if isinstance(v, (int, float)) else str(v).strip()

ZIP_FILE = "secret_key.zip"
st.set_page_config(page_title="Quản lý nhà trọ", layout="centered")
st.title("\U0001F4CA Quản lý nhà trọ với Google Sheet")

pwd = st.text_input("\U0001F510 Nhập mật khẩu file ZIP:", type="password")
if not pwd:
    st.stop()

with tempfile.TemporaryDirectory() as tmpdir:
    try:
        with pyzipper.AESZipFile(ZIP_FILE, 'r') as z:
            z.pwd = pwd.encode()
            z.extractall(tmpdir)
        json_file = next((f for f in os.listdir(tmpdir) if f.endswith(".json")), None)
        if not json_file:
            st.error("❌ Không tìm thấy file .json.")
            st.stop()

        creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(tmpdir, json_file),
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        st.success("✅ Kết nối thành công!")

        sheet_url = st.text_input("\U0001F517 Dán link Google Sheet tại đây:",
                    "https://docs.google.com/spreadsheets/d/1AxkWZAumRsyW8TkxK3-47SrkyoD8mDZKMuaCZ5ebONk/edit?gid=245158288")

        if not sheet_url:
            st.stop()

        sheet = client.open_by_url(sheet_url).sheet1
        df = pd.DataFrame(sheet.get_all_records(empty2zero=False, default_blank=""))
        df = df.loc[:, df.columns.notnull()]
        df = df.dropna(axis=1, how='all')

        if df.empty:
            st.warning("Sheet chưa có dữ liệu.")
            st.stop()

        st.dataframe(df)

        st.subheader("\U0001F4DD Chỉnh sửa dòng")
        idx = st.selectbox("Chọn dòng:", df.index, format_func=lambda i: f"{df.iloc[i]['SO_PHONG']} - {df.iloc[i]['HO_TEN_KHACH_THUE']}")
        row = df.iloc[idx]

        with st.form("form_edit"):
            updated = {col: st.text_input(col, str(row[col])) for col in df.columns}
            update = st.form_submit_button("✅ Cập nhật")
            delete = st.form_submit_button("🗑️ Xoá")

        if update:
            values = [format_value(k, v) for k, v in updated.items()]
            sheet.update(f"A{idx+2}:{colnum_to_excel_col(len(values))}{idx+2}", [values])
            st.success("✔️ Cập nhật xong")
            st.rerun()

        if delete:
            sheet.delete_rows(idx+2)
            st.warning("🗑️ Đã xoá dòng")
            st.rerun()

        with st.expander("➕ Thêm dòng mới"):
            with st.form("form_add"):
                new_row = {col: st.text_input(col, "" if "THANG" in col else str(row[col])) for col in df.columns}
                them = st.form_submit_button("📥 Thêm")
            if them:
                values = [format_value(k, v) for k, v in new_row.items()]
                sheet.append_row(values)
                st.success("✅ Đã thêm dòng mới")
                st.rerun()

        st.subheader("\U0001F4C6 Tạo dữ liệu tháng mới")
        if st.button("➕ Tạo tháng kế tiếp"):
            try:
                df['THANG_parsed'] = pd.to_datetime(df['THANG'], errors='coerce')
                latest = df.sort_values('THANG_parsed').groupby('SO_PHONG').tail(1)
                new_rows = []

                for _, r in latest.iterrows():
                    if pd.isna(r['THANG_parsed']):
                        continue
                    next_month = (r['THANG_parsed'] + pd.DateOffset(months=1)).strftime('%Y-%m')
                    new_r = r.copy()
                    new_r['THANG'] = next_month

                    for col in ['CHI_SO_DIEN_MOI', 'CHI_SO_NUOC_MOI', 'DA_THANH_TOAN', 'NGAY_THANH_TOAN', 'SO_TIEN_DA_TRA', 'HINH_THUC_THANH_TOAN', 'TIEN_DIEN', 'TIEN_NUOC', 'TONG_CONG']:
                        if col in new_r:
                            new_r[col] = ""

                    row_values = [parse_value(col, new_r[col]) for col in df.columns]
                    new_rows.append(row_values)

                if new_rows:
                    sheet.append_rows(new_rows)
                    st.success(f"✅ Đã thêm {len(new_rows)} dòng tháng kế tiếp")
                    st.rerun()
                else:
                    st.warning("⛔ Không có dữ liệu hợp lệ để tạo dòng mới.")
            except Exception as e:
                st.error(f"❌ Lỗi khi tạo dòng mới: {e}")

        st.subheader("⚡ Nhập chỉ số điện nước")
        phong = st.selectbox("Chọn phòng:", df['SO_PHONG'].unique())
        dfp = df[df['SO_PHONG'] == phong].copy()
        dfp['THANG_parsed'] = pd.to_datetime(dfp['THANG'], errors='coerce')
        dfp = dfp.sort_values('THANG_parsed', ascending=False)
        target = dfp[dfp['CHI_SO_DIEN_MOI'].eq("") | dfp['CHI_SO_DIEN_MOI'].isna()].head(1)

        if target.empty:
            st.info("Không có dòng cần nhập chỉ số")
        else:
            target_idx = target.index[0]
            st.write(f"Dòng cần cập nhật: THANG {df.at[target_idx, 'THANG']}")
            with st.form("cs_moi"):
                sodien = st.number_input("Chỉ số điện mới", min_value=0)
                sonuoc = st.number_input("Chỉ số nước mới", min_value=0)
                ok = st.form_submit_button("💾 Cập nhật")
            if ok:
                df.at[target_idx, 'CHI_SO_DIEN_MOI'] = sodien
                df.at[target_idx, 'CHI_SO_NUOC_MOI'] = sonuoc
                row_vals = [format_value(k, df.at[target_idx, k]) for k in df.columns]
                sheet.update(f"A{target_idx+2}:{colnum_to_excel_col(len(row_vals))}{target_idx+2}", [row_vals])
                st.success("✅ Cập nhật xong")
                st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi: {e}")
