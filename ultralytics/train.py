from . import YOLO

# Load mô hình YOLO
model = YOLO("yolov8n.pt")  # Có thể thay đổi sang yolov8s.pt, yolov8m.pt tùy nhu cầu

# Huấn luyện mô hình
model.train(
    data="data.yaml",    # Đường dẫn file data.yaml
    epochs=200,          # Huấn luyện lâu hơn để đạt độ chính xác cao
    imgsz=640,          # Kích thước ảnh (640x640 tối ưu nhất)
    batch=32,           # Batch size lớn tận dụng GPU (Giảm xuống 16 nếu bị thiếu VRAM)
    device="cuda",      # Chạy trên GPU
    workers=8,          # Tận dụng tối đa CPU để load data
    optimizer="AdamW",  # AdamW tối ưu hơn cho bài toán detection
    lr0=0.002,         # Learning rate ban đầu, có thể giảm nếu loss dao động
    momentum=0.937,     # Giá trị mặc định tốt nhất cho YOLO
    weight_decay=0.0005,# Giúp giảm overfitting
    patience=20,        # Dừng sớm nếu sau 20 epochs không cải thiện
    dropout=0.1,        # Tránh overfitting bằng dropout nhẹ
    label_smoothing=0.1 # Giúp mô hình học ổn định hơn
)

