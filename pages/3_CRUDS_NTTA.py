# Quản lý nhà trọ bằng Streamlit + Google Sheet + pyzipper
import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

# Cấu hình Streamlit
st.set_page_config(page_title="Quản lý nhà trọ", layout="wide")
st.title("🏠 Ứng dụng Quản lý Nhà trọ - Kết nối Google Sheet")

# Đường dẫn file ZIP chứa key
ZIP_FILE_PATH = "secret_key.zip"

# Nhập mật khẩu ZIP
st.subheader("🔐 Nhập mật khẩu để giải nén file key:")
zip_password = st.text_input("Mật khẩu ZIP", type="password")

if zip_password:
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Giải nén file ZIP chứa key
            with pyzipper.AESZipFile(ZIP_FILE_PATH, 'r') as zf:
                zf.pwd = zip_password.encode()
                zf.extractall(tmpdir)

            json_files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
            if not json_files:
                st.error("❌ Không tìm thấy file JSON trong file ZIP.")
            else:
                # Load credentials từ file JSON
                json_path = os.path.join(tmpdir, json_files[0])
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
                client = gspread.authorize(creds)

                # Nhập URL Google Sheet
                sheet_url = st.text_input("📄 Dán link Google Sheet:", 
                    "https://docs.google.com/spreadsheets/d/1AxkWZAumRsyW8TkxK3-47SrkyoD8mDZKMuaCZ5ebONk/edit#gid=0")

                def load_data():
                    try:
                        sheet = client.open_by_url(sheet_url).sheet1
                        data = sheet.get_all_records()
                        return pd.DataFrame(data), sheet
                    except Exception as e:
                        st.error("❌ Lỗi khi kết nối Google Sheet.")
                        st.exception(e)
                        return pd.DataFrame(), None

                df, sheet = load_data()
                if not df.empty:
                    st.success("✅ Dữ liệu đã tải thành công!")
                    st.subheader("📋 Dữ liệu Nhà trọ hiện tại")
                    st.dataframe(df, use_container_width=True)

                    st.subheader("🛠️ Chỉnh sửa / Xoá dòng")

                    selected_row = st.selectbox(
                        "Chọn dòng để chỉnh sửa hoặc xoá:",
                        df.index,
                        format_func=lambda i: f"Phòng: {df.iloc[i]['Số phòng']} | Khách: {df.iloc[i]['Họ tên khách thuê']}"
                    )

                    with st.expander("✏️ Chỉnh sửa"):
                        with st.form("form_edit"):
                            edited_row = {}
                            for col in df.columns:
                                edited_row[col] = st.text_input(col, df.iloc[selected_row][col])
                            if st.form_submit_button("✅ Cập nhật"):
                                try:
                                    col_count = len(edited_row)
                                    end_col_letter = chr(65 + col_count - 1)
                                    sheet.update(f"A{selected_row+2}:{end_col_letter}{selected_row+2}", [list(edited_row.values())])
                                    st.success("✅ Cập nhật thành công!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error("❌ Không cập nhật được.")
                                    st.exception(e)

                    with st.expander("🗑️ Xoá dòng"):
                        if st.button("❌ Xác nhận xoá dòng"):
                            try:
                                sheet.delete_rows(selected_row + 2)
                                st.success("🗑️ Đã xoá dòng thành công!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error("❌ Không xoá được.")
                                st.exception(e)
                else:
                    st.warning("⚠️ Không có dữ liệu hoặc không thể tải Google Sheet.")
        except Exception as e:
            st.error("❌ Lỗi khi giải nén hoặc xử lý key.")
            st.exception(e)
