import streamlit as st
# https://pro3rsapp-5mtc9l6ey9fgkhr73dbca9.streamlit.app/
# Cấu hình trang
st.set_page_config(
    page_title="Ứng Dụng QUẢN LÝ NHÀ TRỌ",
    page_icon="🏠",
    layout="centered"
)

# Nội dung trang chủ
st.title("Chào Mừng Đến Với NHÀ TRỌ TIẾN AN")
st.image("image_tt.png", use_column_width=True)

st.markdown("""
## Giới Thiệu NHÀ TRỌ TIẾN AN.

## Hướng Dẫn Sử Dụng
1. 
2. 
3. 
""")
st.markdown("""
### - Facebook:               ............
### - Zalo:                   ............            
## Thành viên:
1. Ngô Duy Tiến
2. Nguyễn Thị Thúy An
3. Ngô Nhã Trang
4. Ngô Nhã Thanh

Ngày BUILD: 25/06/2025            
""")
# Thêm footer  git init
st.divider()
st.caption("© 2025 Bản quyền thuộc về tác giả.")