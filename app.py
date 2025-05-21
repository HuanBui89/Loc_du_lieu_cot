import re
import pandas as pd
import streamlit as st
from io import BytesIO

def parse_data(input_text):
    entries = []
    current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
    
    lines = [line.strip() for line in input_text.split("\n") if line.strip()]
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Xử lý MÃ HÀNG (có thể gộp nhiều mã)
        if re.match(r"(mã|ma|MA|MÃ)\s+\d+", line, re.IGNORECASE):
            if current["Mã hàng"] and (current["SĐT"] or current["Địa chỉ"]):
                entries.append(current)
                current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
            
            # Tách các mã hàng
            ma_list = re.findall(r"\d+", line)
            current["Mã hàng"] = "-".join(ma_list)
            
            # Tách tên nếu có trên cùng dòng
            ten = re.split(r"(mã|ma|MA|MÃ)\s*\d+", line, flags=re.IGNORECASE)[-1].strip()
            if ten and not re.search(r"\d", ten):
                current["Tên"] = ten
            else:
                # Nếu không có tên trên dòng mã, lấy dòng tiếp theo
                if i+1 < len(lines) and not re.search(r"(mã|ma|MA|MÃ)\s+\d+", lines[i+1], re.IGNORECASE):
                    i += 1
                    current["Tên"] = lines[i]
        
        # Xử lý SĐT (10-11 chữ số)
        elif re.search(r"(^|\D)(\d{10,11})(\D|$)", line):
            sdt = re.search(r"(^|\D)(\d{10,11})(\D|$)", line).group(2)
            current["SĐT"] = sdt
        
        # Xử lý THU HỘ
        elif "thu" in line.lower():
            tien = re.search(r"(\d+\.?\d*)\s*k?", line.lower())
            if tien:
                current["Tiền thu hộ"] = tien.group(1) + ("k" if "k" in line.lower() else "")
            
            # Khi gặp "thu" thì coi như đã đủ thông tin
            if current["Mã hàng"]:
                entries.append(current)
                current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
        
        # Xử lý ĐỊA CHỈ (các dòng còn lại)
        else:
            if not current["Tên"] and not current["Mã hàng"] and not any(char.isdigit() for char in line):
                current["Tên"] = line
            elif not re.search(r"(mã|ma|MA|MÃ)\s+\d+", line, re.IGNORECASE):
                if line not in current["Tên"]:  # Tránh lặp lại tên
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
        df = df.drop_duplicates(subset=["Mã hàng"], keep="last")
        
        # Xử lý địa chỉ bị thiếu
        for idx, row in df.iterrows():
            if not row["Địa chỉ"] and idx > 0:
                prev_addr = df.at[idx-1, "Địa chỉ"]
                if prev_addr and len(prev_addr.split()) > 10:  # Nếu địa chỉ trước đó dài
                    df.at[idx, "Địa chỉ"] = prev_addr  # Gán địa chỉ từ bản ghi trước
    
    return df

# Giao diện Streamlit
st.set_page_config(page_title="Công cụ xử lý đơn hàng", page_icon="📦", layout="wide")
st.title("📦 Công cụ xử lý đơn hàng PRO")
st.write("Dán dữ liệu thô vào ô bên dưới để tự động trích xuất thông tin đơn hàng")

# Hiển thị mẫu dữ liệu
with st.expander("📋 Xem định dạng mẫu", expanded=True):
    st.code("""
    Mã 1
    Hồng Ngọc
    ấp kiết lập B xã lâm Tân huyện Thạnh trị tỉnh sóc Trăng
    0336085512
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
                with st.spinner("Đang xử lý dữ liệu..."):
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
        
        # Hiển thị thống kê nhanh
        with st.expander("📊 Thống kê"):
            total_cod = sum(float(str(x).replace('k','')) for x in st.session_state.df["Tiền thu hộ"] if str(x).isdigit() or 'k' in str(x))
            st.write(f"Tổng số đơn: {len(st.session_state.df)}")
            st.write(f"Tổng tiền thu hộ: {total_cod:,.0f}đ")
        
        edited_df = st.data_editor(
            st.session_state.df,
            height=500,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "Tiền thu hộ": st.column_config.NumberColumn(format="%d")
            }
        )
        
        # Xuất file Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            edited_df.to_excel(writer, index=False, sheet_name='Đơn hàng')
        output.seek(0)
        
        st.download_button(
            label="📥 Tải xuống Excel",
            data=output,
            file_name="danh_sach_don_hang_pro.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    elif "df" in st.session_state:
        st.warning("Không tìm thấy đơn hàng nào trong dữ liệu nhập vào")

# Hướng dẫn sử dụng
st.markdown("""
## 📝 Hướng dẫn sử dụng nâng cao

1. **Cải tiến chính trong phiên bản PRO**:
   - Xử lý chính xác hơn các trường hợp tên nằm ở dòng riêng
   - Bắt số điện thoại chính xác hơn (10-11 chữ số)
   - Tự động điền địa chỉ cho các bản ghi bị thiếu
   - Hỗ trợ nhiều định dạng viết "mã" (ma, MA, MÃ)
   - Thêm thống kê tổng số đơn và tổng tiền thu hộ

2. **Cách nhập liệu tối ưu**:
