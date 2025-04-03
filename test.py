import os

# Đường dẫn đến các thư mục chứa file nhãn
label_dirs = [
    "C:/Users/hiuth/Downloads/Bus and truck.v5i.yolov11/train/labels",
    "C:/Users/hiuth/Downloads/Bus and truck.v5i.yolov11/valid/labels",
]  # Thay đổi nếu cần

# Ánh xạ từ dữ liệu mới sang mô hình cũ
mapping = {
    0: 3,  # bus (0) -> bus (3)
    1: 0,  # car (1) -> car (0)
    2: 1,  # motorbike (2) -> motorbike (1)
    3: 2   # truck (3) -> truck (2)
}

# Duyệt qua từng thư mục
for label_dir in label_dirs:
    if not os.path.exists(label_dir):
        print(f"Thư mục {label_dir} không tồn tại, bỏ qua...")
        continue

    # Duyệt qua tất cả các file .txt trong thư mục
    for filename in os.listdir(label_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(label_dir, filename)
            with open(filepath, "r") as f:
                lines = f.readlines()

            # Thay đổi class_id trong từng dòng
            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) == 0:
                    continue
                class_id = int(parts[0])
                new_class_id = mapping[class_id]
                parts[0] = str(new_class_id)
                new_lines.append(" ".join(parts))

            # Ghi lại file
            with open(filepath, "w") as f:
                f.write("\n".join(new_lines))

    print(f"Đã xử lý xong thư mục {label_dir}")