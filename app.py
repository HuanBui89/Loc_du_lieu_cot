import re
import pandas as pd
import streamlit as st

def parse_data(input_text):
    entries = []
    current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
    
    lines = input_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        
        # Xử lý MÃ HÀNG (có thể gộp nhiều mã)
        if re.match(r"mã\s+\d+", line, re.IGNORECASE):
            if current["Mã hàng"]:  # Lưu entry trước đó
                entries.append(current)
                current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
            
            # Tách các mã và ghép lại (vd: "Mã 3 Mã 4" → "3-4")
            ma_list = re.findall(r"\d+", line, re.IGNORECASE)
            current["Mã hàng"] = "-".join(ma_list)
            
            # Tách tên nếu có trên cùng dòng (vd: "MÃ 5... Lê Hướng")
            ten = re.split(r"(mã|mÃ)\s*\d+", line, flags=re.IGNORECASE)[-1].strip()
            if ten and not re.search(r"\d", ten):
                current["Tên"] = ten
        
        # Xử lý SĐT
        elif re.search(r"\d{10,}", line):
            sdt = re.findall(r"\d{10,}", line)[0]
            current["SĐT"] = sdt
        
        # Xử lý THU
        elif "thu" in line.lower():
            tien = re.findall(r"\d+\.?\d*", line)
            if tien:
                current["Tiền thu hộ"] = tien[0] + ("k" if "k" in line.lower() else "")
        
        # Xử lý ĐỊA CHỈ (các dòng còn lại)
        else:
            if line and not current["Tên"]:  # Tên có thể ở dòng riêng
                current["Tên"] = line
            elif line:
                current["Địa chỉ"] += line + " "
    
    if current["Mã hàng"]:
        entries.append(current)
    
    # Tạo DataFrame và định dạng
    df = pd.DataFrame(entries)
    df["Tên người nhận"] = df["Mã hàng"] + "_" + df["Tên"]
    df = df[["Mã hàng", "Tên người nhận", "SĐT", "Địa chỉ", "Tiền thu hộ"]]
    return df

# Giao diện Streamlit
st.title("🔢 Công cụ xử lý đơn hàng")
st.write("Dán dữ liệu thô vào ô bên dưới:")

input_text = st.text_area("Nhập dữ liệu:", height=300)
if st.button("Xử lý"):
    if input_text:
        df = parse_data(input_text)
        st.success("✅ Xử lý thành công!")
        st.dataframe(df)
        
        # Xuất file Excel
        excel_file = df.to_excel(index=False, encoding="utf-8")
        st.download_button(
            label="📥 Tải xuống Excel",
            data=excel_file,
            file_name="ket_qua.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Vui lòng nhập dữ liệu!")

# Hướng dẫn sử dụng
st.markdown("""
### 📝 Hướng dẫn:
1. **Dán dữ liệu** vào ô trên (ví dụ: dữ liệu đơn hàng từ tin nhắn/email).
2. Nhấn **Xử lý** để tự động tách thông tin.
3. **Tải xuống** file Excel nếu cần.
""")
