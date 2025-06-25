# Streamlit App Quản Lý Nhà Trọ với Google Sheet và CRUDS + nhập chỉ số mới + tự động tạo dòng tháng mới
import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- HÀM CHUYỂN SỐ CỘT SANG CHỮ EXCEL (A, B, ..., Z, AA, AB, ...) ---
def colnum_to_excel_col(n):
    name = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        name = chr(65 + r) + name
    return name

# --- CẤU HÌNH ---
ZIP_FILE_PATH = "secret_key.zip"

# --- GIAO DIỆN ---
st.set_page_config(page_title="Quản lý nhà trọ - Google Sheet", layout="centered")
st.title("📄 Ứng dụng quản lý nhà trọ kết nối Google Sheet")

st.subheader("🔐 Nhập mật khẩu để giải nén file key:")
zip_password = st.text_input("Mật khẩu ZIP", type="password")

creds = None

if zip_password:
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            with pyzipper.AESZipFile(ZIP_FILE_PATH, 'r') as zip_ref:
                zip_ref.pwd = zip_password.encode()
                zip_ref.extractall(path=tmpdir)

            json_files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
            if not json_files:
                st.error("❌ Không tìm thấy file .json trong file ZIP.")
            else:
                json_path = os.path.join(tmpdir, json_files[0])
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
                client = gspread.authorize(creds)
                st.success("✅ Đã giải nén và kết nối thành công!")

                sheet_url = st.text_input("🔗 Dán link Google Sheet tại đây:",
                    "https://docs.google.com/spreadsheets/d/1AxkWZAumRsyW8TkxK3-47SrkyoD8mDZKMuaCZ5ebONk/edit#gid=0")

                def load_data():
                    try:
                        sheet = client.open_by_url(sheet_url).sheet1
                        records = sheet.get_all_records()
                        return pd.DataFrame(records), sheet
                    except Exception as e:
                        st.error("❌ Lỗi khi đọc dữ liệu từ Google Sheet.")
                        st.exception(e)
                        return pd.DataFrame(), None

                st.subheader("📥 Dữ liệu hiện tại:")
                df, sheet = load_data()
                if not df.empty:
                    # --- Nhập chỉ số mới ---
                    st.subheader("⚡ Nhập chỉ số điện nước mới")
                    phong_list = df['Số phòng'].unique().tolist()
                    selected_phong = st.selectbox("Chọn số phòng", phong_list)

                    df_phong = df[df['Số phòng'] == selected_phong].copy()
                    try:
                        df_phong['THANG_sort'] = pd.to_datetime(df_phong['THANG'], errors='coerce')
                        df_phong = df_phong.sort_values(by='THANG_sort', ascending=False)
                    except:
                        df_phong = df_phong.sort_values(by='THANG', ascending=False)

                    row_to_update = df_phong[df_phong['Chỉ số điện mới'].isna() | df_phong['Chỉ số điện mới'].eq("")].head(1)

                    if row_to_update.empty:
                        st.info("✅ Không có dòng nào cần nhập chỉ số mới cho phòng này.")
                    else:
                        idx = row_to_update.index[0]
                        row_data = df.loc[idx]
                        st.write(f"Dòng cần cập nhật - THANG: {row_data['THANG']}")
                        with st.form("nhap_chiso_moi"):
                            chisodienmoi = st.number_input("Chỉ số điện mới", min_value=0, value=0)
                            chisonuocmoi = st.number_input("Chỉ số nước mới", min_value=0, value=0)
                            capnhat_btn = st.form_submit_button("💾 Cập nhật")
                            if capnhat_btn:
                                try:
                                    df.at[idx, 'Chỉ số điện mới'] = chisodienmoi
                                    df.at[idx, 'Chỉ số nước mới'] = chisonuocmoi
                                    col_count = len(df.columns)
                                    end_col_letter = colnum_to_excel_col(col_count)
                                    sheet.update(f"A{idx+2}:{end_col_letter}{idx+2}", [[str(x) for x in df.iloc[idx].tolist()]])
                                    st.success("✅ Đã cập nhật chỉ số mới!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Không cập nhật được: {e}")
                else:
                    st.info("Chưa có dữ liệu hoặc không thể tải.")

        except RuntimeError:
            st.error("❌ Mật khẩu ZIP sai hoặc file lỗi.")
        except Exception as e:
            st.error(f"❌ Lỗi khi giải nén hoặc đọc key: {e}")
