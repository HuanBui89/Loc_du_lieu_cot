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
            current["SĐT"] = re.findall(r"\d{10,}", line)[-1]  # Lấy số cuối cùng trong dòng
        
        # Xử lý THU HỘ
        elif "thu" in line.lower():
            tien = re.findall(r"\d+\.?\d*", line)
            if tien:
                current["Tiền thu hộ"] = tien[0] + ("k" if "k" in line.lower() else "")
            
            # Khi gặp "thu" thì coi như đã đủ thông tin
            entries.append(current)
            current = {"Mã hàng": "", "Tên": "", "SĐT": "", "Địa chỉ": "", "Tiền thu hộ": ""}
        
        # Xử lý ĐỊA CHỈ (các dòng còn lại)
        elif line:
            if not current["Tên"] and not current["Mã hàng"]:
                current["Tên"] = line
            else:
                current["Địa chỉ"] += line + " "
        
        i += 1
    
    # Thêm entry cuối cùng nếu còn
    if current["Mã hàng"]:
        entries.append(current)
    
    # Tạo DataFrame và định dạng
    df = pd.DataFrame(entries)
    if not df.empty:
        df["Tên người nhận"] = df["Mã hàng"] + "_" + df["Tên"]
        df = df[["Mã hàng", "Tên người nhận", "SĐT", "Địa chỉ", "Tiền thu hộ"]]
    return df
