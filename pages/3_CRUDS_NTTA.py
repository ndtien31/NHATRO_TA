import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

# --- CẤU HÌNH ---
ZIP_FILE_PATH = "secret_key.zip"  # File ZIP chứa credentials JSON

# --- GIAO DIỆN ---
st.set_page_config(page_title="Quản lý nhà trọ - Google Sheet", layout="centered")
st.title("📄 Ứng dụng quản lý nhà trọ kết nối Google Sheet")

# --- Nhập mật khẩu để giải nén file zip ---
st.subheader("🔐 Nhập mật khẩu để giải nén file key:")
zip_password = st.text_input("Mật khẩu ZIP", type="password")

creds = None

if zip_password:
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Giải nén file ZIP
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
                        st.error("❌ Lỗi khi đọc dữ liệu từ Google Sheet.")
                        st.exception(e)
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
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"❌ Không ghi được: {e}")

                st.subheader("📥 Dữ liệu hiện tại:")
                df, sheet = load_data()
                if not df.empty:
                    st.dataframe(df, use_container_width=True)

                    st.subheader("🛠️ Quản lý dữ liệu (CRUDS)")
                    selected_index = st.selectbox("Chọn dòng để sửa hoặc xóa", df.index, format_func=lambda x: f"Phòng: {df.iloc[x]['Phòng']}")

                    with st.expander("✏️ Sửa dòng"):
                        with st.form("edit_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_room = st.text_input("Phòng", df.iloc[selected_index]["Phòng"])
                                new_name = st.text_input("Họ tên", df.iloc[selected_index]["Họ tên"])
                            with col2:
                                new_phone = st.text_input("SĐT", df.iloc[selected_index]["SĐT"])
                                new_note = st.text_input("Ghi chú", df.iloc[selected_index]["Ghi chú"])

                            if st.form_submit_button("💾 Lưu thay đổi"):
                                try:
                                    sheet.update(f"A{selected_index+2}:D{selected_index+2}", [[new_room, new_name, new_phone, new_note]])
                                    st.success("✅ Đã cập nhật thành công!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"❌ Không cập nhật được: {e}")

                    with st.expander("🗑️ Xoá dòng"):
                        if st.button("❌ Xoá dòng đã chọn"):
                            try:
                                sheet.delete_rows(selected_index + 2)
                                st.success("✅ Đã xoá dòng thành công!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"❌ Không xoá được: {e}")

                    with st.expander("🔍 Tìm kiếm"):
                        keyword = st.text_input("🔎 Nhập từ khoá (tên, số điện thoại, ghi chú,...):")
                        if keyword:
                            filtered_df = df[df.apply(lambda row: keyword.lower() in str(row).lower(), axis=1)]
                            st.dataframe(filtered_df if not filtered_df.empty else "⛔ Không tìm thấy kết quả.")
                else:
                    st.info("Chưa có dữ liệu hoặc không thể tải.")

        except RuntimeError:
            st.error("❌ Mật khẩu ZIP sai hoặc file lỗi.")
        except Exception as e:
            st.error(f"❌ Lỗi khi giải nén hoặc đọc key: {e}")
