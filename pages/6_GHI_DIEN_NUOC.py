# Streamlit App Quản Lý Nhà Trọ với Google Sheet và CRUDS + nhập chỉ số mới
import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

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
                    selected_row = st.selectbox("📝 Chọn dòng để chỉnh sửa, xoá hoặc tạo mới từ dòng này:", df.index, format_func=lambda i: f"Phòng: {df.iloc[i]['Số phòng']} - Khách: {df.iloc[i]['Họ tên khách thuê']}")
                    selected_data = df.iloc[selected_row]

                    with st.expander("✏️ Chỉnh sửa dòng đã chọn"):
                        with st.form("edit_form"):
                            edited_row = {}
                            for col in df.columns:
                                edited_row[col] = st.text_input(col, value=str(selected_data[col]))
                            update_btn = st.form_submit_button("✅ Cập nhật dòng")
                            delete_btn = st.form_submit_button("🗑️ Xoá dòng")

                        if update_btn:
                            try:
                                col_count = len(edited_row)
                                end_col_letter = colnum_to_excel_col(col_count)
                                sheet.update(f"A{selected_row+2}:{end_col_letter}{selected_row+2}", [list(edited_row.values())])
                                st.success("✅ Cập nhật thành công!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Lỗi khi cập nhật: {e}")

                        if delete_btn:
                            try:
                                sheet.delete_rows(selected_row + 2)
                                st.success("🗑️ Đã xoá dòng!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Lỗi khi xoá: {e}")

                    with st.expander("➕ Thêm dòng mới từ dòng đã chọn"):
                        with st.form("duplicate_form"):
                            new_row = {}
                            for col in df.columns:
                                default = str(selected_data[col]) if "THANG" not in col else ""
                                new_row[col] = st.text_input(f"{col}", value=default)
                            if st.form_submit_button("📥 Thêm dòng mới"):
                                try:
                                    sheet.append_row(list(new_row.values()))
                                    st.success("✅ Đã thêm dòng mới từ dữ liệu cũ!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Không thêm được: {e}")

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
                                    sheet.update(f"A{idx+2}:{end_col_letter}{idx+2}", [df.iloc[idx].tolist()])
                                    st.success("✅ Đã cập nhật chỉ số mới!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Không cập nhật được: {e}")

                    st.dataframe(df, use_container_width=True)

                else:
                    st.info("Chưa có dữ liệu hoặc không thể tải.")

        except RuntimeError:
            st.error("❌ Mật khẩu ZIP sai hoặc file lỗi.")
        except Exception as e:
            st.error(f"❌ Lỗi khi giải nén hoặc đọc key: {e}")
