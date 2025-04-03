import os
import shutil
import random

# Đường dẫn đến thư mục chứa dữ liệu gộp và các thư mục đích
all_data_dir = "C:/Users/hiuth/Downloads/all_data"
base_dir = "C:/Users/hiuth/Downloads/New_data"

# Tạo các thư mục train, valid, test và các thư mục con images, labels
dirs = ["train", "valid", "test"]
for dir_name in dirs:
    os.makedirs(os.path.join(base_dir, dir_name, "images"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, dir_name, "labels"), exist_ok=True)

# Lấy danh sách tất cả file ảnh
image_files = [f for f in os.listdir(all_data_dir) if f.endswith('.jpg')]  # Thay '.jpg' nếu ảnh có định dạng khác

# Xáo trộn danh sách file
random.shuffle(image_files)

# Tính số lượng file cho từng tập
total_files = len(image_files)
train_ratio = 0.7  # 70%
valid_ratio = 0.15  # 15%
test_ratio = 0.15  # 15%

train_count = int(total_files * train_ratio)
valid_count = int(total_files * valid_ratio)
test_count = total_files - train_count - valid_count  # Đảm bảo không bỏ sót file

# Chia file vào các tập
train_files = image_files[:train_count]
valid_files = image_files[train_count:train_count + valid_count]
test_files = image_files[train_count + valid_count:]

# Hàm copy file vào thư mục images và labels
def copy_files(file_list, source_dir, dest_dir):
    for file_name in file_list:
        # Copy ảnh vào thư mục images
        shutil.copy(os.path.join(source_dir, file_name), os.path.join(dest_dir, "images", file_name))
        # Copy nhãn vào thư mục labels (giả sử nhãn có đuôi .txt)
        label_name = file_name.replace('.jpg', '.txt')
        if os.path.exists(os.path.join(source_dir, label_name)):
            shutil.copy(os.path.join(source_dir, label_name), os.path.join(dest_dir, "labels", label_name))

# Copy file vào các thư mục tương ứng
copy_files(train_files, all_data_dir, os.path.join(base_dir, "train"))
copy_files(valid_files, all_data_dir, os.path.join(base_dir, "valid"))
copy_files(test_files, all_data_dir, os.path.join(base_dir, "test"))

print("Chia dữ liệu hoàn tất!")
print(f"Số lượng file trong train: {len(train_files)}")
print(f"Số lượng file trong valid: {len(valid_files)}")
print(f"Số lượng file trong test: {len(test_files)}")