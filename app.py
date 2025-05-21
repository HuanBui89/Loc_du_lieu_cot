import re
import pandas as pd
import streamlit as st
from io import BytesIO

def parse_data(input_text):
    try:
        entries = []
        current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
        
        lines = input_text.strip().split("\n")
        for line in lines:
            line = line.strip()
            
            # Xử lý MÃ HÀNG
            if re.match(r"mã\s+\d+", line, re.IGNORECASE):
                if current["Mã hàng"]:
                    entries.append(current)
                    current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
                
                ma_list = re.findall(r"\d+", line, re.IGNORECASE)
                current["Mã hàng"] = "-".join(ma_list)
                
                ten = re.split(r"(mã|mÃ)\s*\d+", line, flags=re.IGNORECASE)[-1].strip()
                if ten and not re.search(r"\d", ten):
                    current["Tên"] = ten
            
            # Xử lý SĐT
            elif re.search(r"\d{10,}", line):
                sdt = re.findall(r"\d{10,}", line)[0]
                current["SĐT"] = sdt
            
            # Xử lý THU HỘ
            elif "thu" in line.lower():
                tien = re.findall(r"\d+\.?\d*", line)
                if tien:
                    current["Tiền thu hộ"] = tien[0] + ("k" if "k" in line.lower() else "")
            
            # Xử lý thông tin khác
            else:
                if line and not current["Tên"]:
                    current["Tên"] = line
                elif line:
                    current["Địa chỉ"] += line + " "
        
        if current["Mã hàng"]:
            entries.append(current)
        
        df = pd.DataFrame(entries)
        if not df.empty:
            df["Tên người nhận"] = df["Mã hàng"] + "_" + df["Tên"]
            df = df[["Mã hàng", "Tên người nhận", "SĐT", "Địa chỉ", "Tiền thu hộ"]]
        return df
    
    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu: {str(e)}")
        return pd.DataFrame()

# Giao diện cải tiến
st.title("🔢 Công cụ xử lý đơn hàng")
st.write("Dán dữ liệu thô vào ô bên dưới:")

# Hiển thị mẫu dữ liệu
with st.expander("📋 Xem định dạng mẫu"):
    st.write("""
    ```
    Mã 123 Nguyễn Văn A
    0987654321
    123 Đường ABC, Quận 1
    Thu 150k
    
    Mã 456 Mã 789 Trần Thị B
    0123456789
    456 Đường XYZ, Quận 2
    Thu 200
    ```
    """)

input_text = st.text_area("Nhập dữ liệu:", height=300, key="input_data")

col1, col2 = st.columns(2)
with col1:
    if st.button("Xử lý", type="primary"):
        if input_text:
            df = parse_data(input_text)
            st.session_state.df = df
        else:
            st.warning("Vui lòng nhập dữ liệu!")

with col2:
    if st.button("Xóa dữ liệu"):
        st.session_state.input_data = ""
        st.session_state.df = pd.DataFrame()
        st.rerun()

if "df" in st.session_state and not st.session_state.df.empty:
    st.success("✅ Xử lý thành công!")
    edited_df = st.data_editor(st.session_state.df)
    
    # Xuất file Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        edited_df.to_excel(writer, index=False, sheet_name='Đơn hàng')
    output.seek(0)
    
    st.download_button(
        label="📥 Tải xuống Excel",
        data=output,
        file_name="danh_sach_don_hang.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
