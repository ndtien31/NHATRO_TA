import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

# Cấu hình trang
st.set_page_config(page_title="Đọc Google Sheet", layout="centered")
st.title("📄 Ứng dụng đọc dữ liệu từ Google Sheet")

# --- CẤU HÌNH ---
ZIP_FILE_PATH = "secret_key.zip"  # file zip có sẵn trên server

# --- Nhập mật khẩu giải nén ---
st.subheader("🔐 Nhập mật khẩu để giải nén file key:")
zip_password = st.text_input("Mật khẩu ZIP", type="password")

creds = None  # sẽ được gán sau nếu giải nén thành công

if zip_password:
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Giải nén file ZIP có sẵn trên server
            with pyzipper.AESZipFile(ZIP_FILE_PATH, 'r') as zip_ref:
                zip_ref.pwd = zip_password.encode()
                zip_ref.extractall(path=tmpdir)

            # Tìm file JSON trong thư mục tạm
            json_files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
            if not json_files:
                st.error("❌ Không tìm thấy file .json trong file ZIP.")
            else:
                json_path = os.path.join(tmpdir, json_files[0])
                scope = [
                    "https://spreadsheets.google.com/feeds",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
                client = gspread.authorize(creds)
                st.success("✅ Đã giải nén và kết nối thành công!")

                # --- Nhập URL Google Sheet ---
                sheet_url = st.text_input("🔗 Dán link Google Sheet tại đây:",
                    "https://docs.google.com/spreadsheets/d/1AxkWZAumRsyW8TkxK3-47SrkyoD8mDZKMuaCZ5ebONk/edit#gid=0")

                def load_data():
                    try:
                        sheet = client.open_by_url(sheet_url).sheet1
                        records = sheet.get_all_records()
                        return pd.DataFrame(records), sheet
                    except Exception as e:
                        st.error("❌ Đã xảy ra lỗi khi đọc dữ liệu.")
                        st.exception(e)  # ✅ In chi tiết lỗi với traceback
                        return pd.DataFrame(), None

                st.subheader("➕ Nhập dữ liệu mới vào Sheet")
                with st.form("add_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        room = st.text_input("Phòng")
                        name = st.text_input("Họ tên")
                    with col2:
                        phone = st.text_input("SĐT")
                        note = st.text_input("Ghi chú")
                    submitted = st.form_submit_button("📤 Ghi vào Sheet")
                    if submitted:
                        df, sheet = load_data()
                        if sheet:
                            try:
                                sheet.append_row([room, name, phone, note])
                                st.success("✅ Ghi dữ liệu thành công!")
                            except Exception as e:
                                st.error(f"❌ Không ghi được: {e}")

                st.subheader("📥 Dữ liệu hiện tại:")
                df, _ = load_data()
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Chưa có dữ liệu hoặc không thể tải.")

        except RuntimeError as e:
            st.error("❌ Mật khẩu ZIP sai hoặc file lỗi.")
        except Exception as e:
            st.error(f"❌ Lỗi khi giải nén hoặc đọc key: {e}")
