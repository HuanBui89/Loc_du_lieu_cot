import re
import pandas as pd
import streamlit as st
from io import BytesIO

def parse_data(input_text):
    entries = []
    current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
    
    lines = input_text.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Xử lý MÃ HÀNG (có thể gộp nhiều mã)
        if re.match(r"mã\s+\d+", line, re.IGNORECASE):
            if current["Mã hàng"]:  # Lưu entry trước đó
                if current["SĐT"] or current["Địa chỉ"]:  # Chỉ thêm nếu có thông tin
                    entries.append(current)
                current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
            
            # Tách các mã hàng
            ma_list = re.findall(r"\d+", line, re.IGNORECASE)
            current["Mã hàng"] = "-".join(ma_list)
            
            # Tách tên nếu có trên cùng dòng
            ten = re.split(r"mã\s*\d+", line, flags=re.IGNORECASE)[-1].strip()
            if ten and not re.search(r"\d", ten):
                current["Tên"] = ten
            else:
                # Nếu không có tên trên dòng mã, lấy dòng tiếp theo
                i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
                if i < len(lines) and not re.search(r"\d{10,}", lines[i]) and "thu" not in lines[i].lower():
                    current["Tên"] = lines[i].strip()
                    i += 1
                else:
                    i -= 1
        
        # Xử lý SĐT (ưu tiên số gần nhất trước "thu")
        elif re.search(r"\d{10,}", line):
            sdt = re.findall(r"\d{10,}", line)
            if sdt:
                current["SĐT"] = sdt[-1]  # Lấy số cuối cùng trong dòng
        
        # Xử lý THU HỘ
        elif "thu" in line.lower():
            tien = re.findall(r"\d+\.?\d*", line)
            if tien:
                current["Tiền thu hộ"] = tien[0] + ("k" if "k" in line.lower() else "")
            
            # Khi gặp "thu" thì coi như đã đủ thông tin
            if current["Mã hàng"]:  # Chỉ thêm nếu có mã hàng
                entries.append(current)
            current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
        
        # Xử lý ĐỊA CHỈ (các dòng còn lại)
        elif line:
            if not current["Tên"] and not current["Mã hàng"] and not any(char.isdigit() for char in line):
                current["Tên"] = line
            else:
                current["Địa chỉ"] += line + " "
        
        i += 1
    
    # Thêm entry cuối cùng nếu còn
    if current["Mã hàng"] and (current["SĐT"] or current["Địa chỉ"]):
        entries.append(current)
    
    # Tạo DataFrame và định dạng
    df = pd.DataFrame(entries)
    if not df.empty:
        df["Tên người nhận"] = df["Mã hàng"] + "_" + df["Tên"]
        df = df[["Mã hàng", "Tên người nhận", "SĐT", "Địa chỉ", "Tiền thu hộ"]]
        df = df.drop_duplicates(subset=["Mã hàng"], keep="last")  # Loại bỏ trùng lặp
    return df

# Giao diện Streamlit
st.set_page_config(page_title="Công cụ xử lý đơn hàng", page_icon="📦", layout="wide")
st.title("📦 Công cụ xử lý đơn hàng")
st.write("Dán dữ liệu thô vào ô bên dưới để tự động trích xuất thông tin đơn hàng")

# Hiển thị mẫu dữ liệu
with st.expander("📋 Xem định dạng mẫu", expanded=True):
    st.code("""
    Mã 1
    Hồng Ngọc
    ấp kiết lập B xã lâm Tân huyện Thạnh trị tỉnh sóc Trăng
    0336085512 người nhận đẹt xăng
    thu: 300
    
    mã 7
    LÊ VĂN THUẬN
    Thành phố Phan Thiết đường Hải Thượng lãn ông phường Phú tài số nhà 340
    0365733739
    Thu: 500
    """)

# Tạo 2 cột
col1, col2 = st.columns([3, 2])

with col1:
    input_text = st.text_area("Nhập dữ liệu:", height=300, key="input_data", 
                            placeholder="Dán dữ liệu đơn hàng vào đây...")
    
    # Nút xử lý và xóa
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🔄 Xử lý dữ liệu", type="primary", use_container_width=True):
            if input_text.strip():
                st.session_state.df = parse_data(input_text)
                st.rerun()
            else:
                st.warning("Vui lòng nhập dữ liệu!")
    with btn_col2:
        if st.button("❌ Xóa dữ liệu", use_container_width=True):
            st.session_state.input_data = ""
            st.session_state.df = pd.DataFrame()
            st.rerun()

with col2:
    if "df" in st.session_state and not st.session_state.df.empty:
        st.success(f"✅ Đã xử lý thành công {len(st.session_state.df)} đơn hàng!")
        edited_df = st.data_editor(
            st.session_state.df,
            height=500,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True
        )
        
        # Xuất file Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='Đơn hàng')
        output.seek(0)
        
        st.download_button(
            label="📥 Tải xuống Excel",
            data=output,
            file_name="danh_sach_don_hang.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    elif "df" in st.session_state:
        st.warning("Không tìm thấy đơn hàng nào trong dữ liệu nhập vào")

# Hướng dẫn sử dụng
st.markdown("""
## 📝 Hướng dẫn sử dụng

1. **Nhập liệu**:
   - Dán dữ liệu đơn hàng vào ô bên trái
   - Mỗi đơn hàng có thể bao gồm:
     - Dòng bắt đầu bằng "Mã X" (X là số)
     - Tên người nhận (có thể trên cùng dòng mã hoặc dòng riêng)
     - Địa chỉ (1 hoặc nhiều dòng)
     - Số điện thoại (10-11 chữ số)
     - Dòng chứa "thu" + số tiền

2. **Chức năng**:
   - Nhấn "Xử lý dữ liệu" để phân tích
   - Chỉnh sửa trực tiếp trên bảng kết quả
   - Tải xuống file Excel khi hoàn tất
   - Nhấn "Xóa dữ liệu" để làm mới

3. **Lưu ý**:
   - Ứng dụng tự động nhận diện thông tin theo thứ tự
   - Có thể xử lý cùng lúc nhiều đơn hàng
   - Đảm bảo dữ liệu nhập vào có định dạng tương tự mẫu
""")
