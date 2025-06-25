import streamlit as st
from PIL import Image

# Cấu hình trang
st.set_page_config(
    page_title="Nhà Trọ Tiến An",
    page_icon="🏠",
    layout="wide"
)

# CSS tùy chỉnh
st.markdown("""
<style>
    .title {
        color: #FF4B4B;
        text-align: center;
        font-size: 2.5em;
    }
    .highlight {
        background-color: #FFF4F4;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .feature-icon {
        font-size: 1.2em;
        color: #FF4B4B;
        margin-right: 8px;
    }
    .contact-box {
        background-color: #FF4B4B;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="title">NHÀ TRỌ TIẾN AN</h1>', unsafe_allow_html=True)
st.markdown("### Nơi an cư lý tưởng cho sinh viên và người đi làm")

# Banner (thay bằng ảnh thực tế)
# img = Image.open("banner_tienan.jpg")
# st.image(img, use_column_width=True)

# Giới thiệu
with st.container():
    st.markdown("""
    <div class="highlight">
        Nằm tại <strong>TP. Thủ Dầu Một, Bình Dương</strong>, Nhà Trọ Tiến An mang đến không gian sống tiện nghi, 
        an toàn với mức giá phải chăng. Với vị trí thuận lợi gần các trường đại học và khu công nghiệp, 
        chúng tôi tự hào là lựa chọn hàng đầu của sinh viên và công nhân.
    </div>
    """, unsafe_allow_html=True)

# Ưu điểm nổi bật
st.header("✨ Ưu điểm nổi bật")
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    - <span class="feature-icon">📍</span> **Vị trí đắc địa** - Gần trường học, khu công nghiệp
    - <span class="feature-icon">🛏️</span> **Phòng chất lượng** - Nội thất đầy đủ, wifi tốc độ cao
    - <span class="feature-icon">🍳</span> **Tiện ích đầy đủ** - Bếp chung, giặt phơi riêng
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    - <span class="feature-icon">🔒</span> **An ninh 24/7** - Camera, khóa vân tay
    - <span class="feature-icon">💰</span> **Giá cả hợp lý** - Nhiều mức giá linh hoạt
    - <span class="feature-icon">🌳</span> **Môi trường xanh** - Không gian thoáng mát
    """, unsafe_allow_html=True)

# Gallery ảnh (thay bằng ảnh thực tế)
st.header("📸 Hình ảnh nhà trọ")
# Tạo 3 cột cho gallery
cols = st.columns(3)
# for i, col in enumerate(cols):
#     img = Image.open(f"phong_{i+1}.jpg")
#     col.image(img, caption=f"Phòng {i+1}")

# Bảng giá
st.header("💵 Bảng giá tham khảo")
price_data = {
    "Loại phòng": ["Phòng đơn", "Phòng đôi", "Phòng cao cấp"],
    "Diện tích": ["18-20m²", "25-28m²", "30-35m²"],
    "Giá thuê": ["1.500.000đ", "2.200.000đ", "2.800.000đ"],
    "Tiện ích": ["Điều hòa, nóng lạnh", "Đầy đủ nội thất", "Ban công riêng"]
}
st.table(price_data)

# Thông tin liên hệ
st.header("📞 Liên hệ đặt phòng")
with st.container():
    st.markdown("""
    <div class="contact-box">
        <h3>NHÀ TRỌ TIẾN AN</h3>
        <p>📍 Địa chỉ: Số 123, đường ABC, TP. Thủ Dầu Một</p>
        <p>📞 Hotline: 0909.123.456</p>
        <p>📧 Email: nhatrotienan@gmail.com</p>
        <p>💻 Fanpage: fb.com/nhatrotienan</p>
    </div>
    """, unsafe_allow_html=True)

# Bản đồ
st.header("🗺️ Vị trí nhà trọ")
# st.map()  # Có thể thêm tọa độ thực tế

# Form liên hệ
with st.expander("📝 Đăng ký xem phòng"):
    with st.form("contact_form"):
        name = st.text_input("Họ và tên")
        phone = st.text_input("Số điện thoại")
        room_type = st.selectbox("Loại phòng quan tâm", ["Phòng đơn", "Phòng đôi", "Phòng cao cấp"])
        visit_date = st.date_input("Ngày muốn xem phòng")
        
        submitted = st.form_submit_button("Gửi yêu cầu")
        if submitted:
            st.success("Cảm ơn bạn! Chúng tôi sẽ liên hệ lại sớm nhất.")