import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pyzipper, tempfile, os, shutil
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# --- CẤU HÌNH ---
ZIP_FILE_PATH = "secret_key.zip"
SAVE_FOLDER = "phieu_thu"
EMAIL_SENDER = "ndtien31@gmail.com"
EMAIL_PASSWORD = "kapdlwqhhktxmlka"  # Mật khẩu ứng dụng Gmail
TEMPLATE_IMAGE = "phieu_template.png"
FONT_PATH = "timesbd.ttf"  # hoặc Roboto nếu bạn có

# --- GIAO DIỆN ---
st.set_page_config(page_title="Gửi phiếu thu", layout="centered")
st.title("📨 Gửi phiếu thu từ Google Sheet + tạo ảnh từ template")

zip_password = st.text_input("🔐 Mật khẩu file ZIP:", type="password")
sheet_url = st.text_input("🔗 Dán link Google Sheet tại đây:",
    "https://docs.google.com/spreadsheets/d/1AxkWZAumRsyW8TkxK3-47SrkyoD8mDZKMuaCZ5ebONk/edit?gid=245158288")

# --- BẮT ĐẦU QUY TRÌNH ---
if zip_password and sheet_url:
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Giải nén file ZIP chứa credentials
            with pyzipper.AESZipFile(ZIP_FILE_PATH, 'r') as zf:
                zf.pwd = zip_password.encode()
                zf.extractall(tmpdir)

            json_files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
            if not json_files:
                st.error("❌ Không có file .json trong ZIP.")
                st.stop()

            # Kết nối Google Sheet
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                os.path.join(tmpdir, json_files[0]),
                ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            )
            client = gspread.authorize(creds)
            sheet = client.open_by_url(sheet_url).sheet1
            df = pd.DataFrame(sheet.get_all_records())

            # Chuẩn hóa tên cột
            df.columns = [col.strip().upper().replace(" ", "_").replace("Đ", "D").replace("Ơ", "O") for col in df.columns]

            # Tìm tháng mới nhất
            df['THANG_DATE'] = pd.to_datetime(df['THANG'], errors='coerce')
            latest_month = df['THANG_DATE'].max()
            df_latest = df[df['THANG_DATE'] == latest_month]

            unpaid = df_latest[df_latest['DA_THANH_TOAN'].astype(str).str.strip().str.lower().isin(['', 'chua', 'no', 'none'])]

            st.subheader(f"📆 Tháng mới nhất: {latest_month.strftime('%Y-%m') if pd.notnull(latest_month) else 'N/a'}")
            st.write(f"Tổng {len(unpaid)} phiếu chưa thanh toán")

            if os.path.exists(SAVE_FOLDER):
                shutil.rmtree(SAVE_FOLDER)
            os.makedirs(SAVE_FOLDER, exist_ok=True)

            if st.button("🚀 Tạo & hiển thị phiếu"):
                for _, row in unpaid.iterrows():
                    email = row.get("EMAIL", "").strip()
                    room = str(row.get("SO_PHONG", "")).strip()
                    month = row.get("THANG", "")
                    name = row.get("HO_TEN_KHACH_THUE", "Khách")
                    filename = f"{room}_{name}_{month}".replace("/", "").replace("\\", "").strip() + ".png"
                    filepath = os.path.join(SAVE_FOLDER, filename)

                    bg = Image.open(TEMPLATE_IMAGE).convert("RGB")
                    draw = ImageDraw.Draw(bg)
                    try:
                        font = ImageFont.truetype(FONT_PATH, 15)
                        font_bold = ImageFont.truetype(FONT_PATH, 15)
                        font_bold_tong = ImageFont.truetype(FONT_PATH, 18)
                    except:
                        font = ImageFont.load_default()
                        font_bold = font

                    # Vẽ nội dung lên ảnh
                    
                    month_only = month.split("/")[1]  # Lấy phần thứ 2 (tháng)
                    draw.text((206, 110), f"THÁNG {month_only}", font=font_bold, fill="#FF1493")
                    draw.text((365, 155), f"PHÒNG {room}", font=font_bold, fill="#096106")
                    draw.text((206, 90), f"KH: {name.upper()}", font=font_bold_tong, fill="#FF1493")

                    cs_dien_moi = int(row.get('CHI_SO_DIEN_MOI', 0))
                    cs_dien_cu = int(row.get('CHI_SO_DIEN_CU', 0))
                    so_dien = cs_dien_moi - cs_dien_cu
                    gia_dien = int(row.get('GIA_DIEN', 0))
                    tien_dien = row.get('TIEN_DIEN', 0)

                    draw.text((250, 210),  f"{cs_dien_cu:,}", font=font, fill="black", anchor="ra")
                    draw.text((320, 210), f"{cs_dien_moi:,}", font=font, fill="black", anchor="ra")
                    draw.text((420, 210), str(so_dien), font=font, fill="black", anchor="ra")
                    draw.text((500, 210), f"{gia_dien:,}", font=font, fill="black", anchor="ra")
                    draw.text((600, 210), f"{int(tien_dien):,}", font=font, fill="black", anchor="ra")

                    cs_nuoc_moi = int(row.get('CHI_SO_NUOC_MOI', 0))
                    cs_nuoc_cu = int(row.get('CHI_SO_NUOC_CU', 0))
                    so_nuoc = cs_nuoc_moi - cs_nuoc_cu
                    gia_nuoc = int(row.get('GIA_NUOC', 0))
                    tien_nuoc = row.get('TIEN_NUOC', 0)
                    draw.text((250, 227), str(cs_nuoc_cu), font=font, fill="black", anchor="ra")
                    draw.text((320, 227), str(cs_nuoc_moi), font=font, fill="black", anchor="ra")
                    draw.text((420, 227), str(so_nuoc), font=font, fill="black", anchor="ra")    
                    draw.text((500, 227), f"{gia_nuoc:,}", font=font, fill="black", anchor="ra")                   
                    draw.text((600, 227), f"{int(tien_nuoc):,}", font=font, fill="black", anchor="ra")

                    #draw.text((530, 266), f"{int(row.get('TIEN_DICH_VU', 0)):,}", font=font, fill="black")
                    draw.text((600, 246), f"{int(row.get('TIEN_RAC', 0)):,}", font=font, fill="black", anchor="ra")
                    draw.text((600,265 ), f"{int(row.get('TIEN_THUE_PHONG', 0)):,}", font=font_bold, fill="black", anchor="ra")

                    draw.text((600, 283), f"{int(row.get('TONG_CONG', 0)):,}", font=font_bold_tong, fill="red", anchor="ra")

                    #ghi_chu = row.get("GHI_CHU", "").strip()
                    #if ghi_chu:
                    #    draw.text((100, 360), f"Ghi chú: {ghi_chu}", font=font, fill="blue")

                    bg.save(filepath)

                # Hiển thị danh sách ảnh
                st.subheader("🖼️ Danh sách phiếu thu đã tạo:")
                for img_file in os.listdir(SAVE_FOLDER):
                    if img_file.endswith(".png"):
                        st.image(os.path.join(SAVE_FOLDER, img_file), caption=img_file, width=600)

        except Exception as e:
            st.error(f"❌ Lỗi hệ thống: {e}")
