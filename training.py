# train_yolo.py

from ultralytics import YOLO

if __name__ == '__main__':
    # Tải mô hình từ file trọng số
    model = YOLO('yolov8n.pt')  # Thay đổi đường dẫn nếu cần
#runs/detect/train24/weights/best.pt
    # Huấn luyện mô hình
    model.train(
            data='data3.yaml',
            epochs=200,  # Giảm epoch để thử nghiệm
            imgsz=640,   # Giảm kích thước ảnh để tăng tốc
            patience=30,
            batch=64,    # Tăng batch size (thử 64 nếu VRAM đủ)
            device=0,    # Sử dụng GPU 0
            workers=4,  # Tận dụng CPU đa nhân
            amp=True,    # Sử dụng mixed precision
            augment=True,
            save_period=10
        )
    #hỏi AI: cách để cải thiện việc nhận diện nhanh hơn và chính xác hơn