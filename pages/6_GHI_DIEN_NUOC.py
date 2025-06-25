# Streamlit App Quản Lý Nhà Trọ với Google Sheet và CRUDS + nhập chỉ số mới + tự động tạo dòng tháng mới + chuẩn hoá cột ngày
import streamlit as st
import pandas as pd
import gspread
import os
import pyzipper
import tempfile
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- HÀM CHUYỂN SỐ CỘT SANG CHỮ EXCEL (A, B, ..., Z, AA, AB, ...) ---
def colnum_to_excel_col(n):
    name = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        name = chr(65 + r) + name
    return name

# --- HÀM CHUẨN HOÁ NGÀY ---
def normalize_dates(row, date_cols):
    for col in date_cols:
        if col in row and row[col]:
            try:
                row[col] = pd.to_datetime(row[col], errors='coerce').strftime("%Y-%m-%d")
            except:
                pass
    if 'THANG' in row and row['THANG']:
        try:
            row['THANG'] = pd.to_datetime(row['THANG'], errors='coerce').strftime("%Y-%m")
        except:
            pass
    return row

# --- CẤU HÌNH ---
ZIP_FILE_PATH = "secret_key.zip"
DATE_COLUMNS = ['Ngày sinh', 'Ngày bắt đầu HĐ', 'Ngày kết thúc HĐ', 'Ngày thanh toán']

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

                st.subheader("📥 THÊM KHÁCH HÀNG MỚI:")
                df, sheet = load_data()
                if not df.empty:
                    selected_row = st.selectbox("📝 Chọn dòng để tạo mới từ dòng này:", df.index, format_func=lambda i: f"Phòng: {df.iloc[i]['Số phòng']} - Khách: {df.iloc[i]['Họ tên khách thuê']}")
                    selected_data = df.iloc[selected_row]

                    with st.expander("➕ Thêm dòng mới từ dòng đã chọn"):
                        with st.form("duplicate_form"):
                            new_row = {}
                            for col in df.columns:
                                default = str(selected_data[col]) if "THANG" not in col else ""
                                new_row[col] = st.text_input(f"{col}", value=default)
                            if st.form_submit_button("📥 Thêm dòng mới"):
                                try:
                                    new_row = normalize_dates(new_row, DATE_COLUMNS)
                                    sheet.append_row([str(v) for v in new_row.values()])
                                    st.success("✅ Đã thêm dòng mới từ dữ liệu cũ!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Không thêm được: {e}")

                    st.subheader("📆 TẠO DỮ LIỆU THU THÁNG MỚI")
                    if st.button("➕ Tạo dữ liệu tháng mới"):
                        try:
                            df['THANG_date'] = pd.to_datetime(df['THANG'], errors='coerce')
                            latest_rows = df.sort_values('THANG_date').groupby('Số phòng').tail(1)

                            new_rows = []
                            for _, row in latest_rows.iterrows():
                                new_row = row.copy()
                                if pd.isna(new_row['THANG_date']):
                                    continue
                                next_month = new_row['THANG_date'] + pd.DateOffset(months=1)
                                new_row['THANG'] = next_month.strftime("%Y-%m")
                                for col in ['Chỉ số điện mới', 'Chỉ số nước mới', 'Đã thanh toán', 'Ngày thanh toán', 'Số tiền đã trả', 'Hình thức thanh toán', 'Tiền điện', 'Tiền nước', 'Tổng cộng']:
                                    if col in new_row:
                                        new_row[col] = ""
                                new_row = normalize_dates(new_row, DATE_COLUMNS)
                                new_rows.append([str(x) for x in new_row[df.columns].tolist()])

                            if new_rows:
                                sheet.append_rows(new_rows)
                                st.success(f"✅ Đã tạo {len(new_rows)} dòng mới cho tháng kế tiếp.")
                                st.rerun()
                            else:
                                st.warning("⛔ Không có dữ liệu hợp lệ để tạo dòng mới.")
                        except Exception as e:
                            st.error(f"❌ Tạo dữ liệu tháng mới: {e}")

                    st.dataframe(df, use_container_width=True)

                else:
                    st.info("Chưa có dữ liệu hoặc không thể tải.")

        except RuntimeError:
            st.error("❌ Mật khẩu ZIP sai hoặc file lỗi.")
        except Exception as e:
            st.error(f"❌ Lỗi khi giải nén hoặc đọc key: {e}")