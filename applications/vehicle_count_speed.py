import cv2
from ultralytics import YOLO
import numpy as np
import os
import uuid
from datetime import datetime
from database import get_video_path
from ultralytics.solutions import speed_estimation

def generate_output_filename(input_filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    extension = os.path.splitext(input_filename)[1]
    return f"processed_video_{timestamp}_{unique_id}{extension}"

def vehicle_count_and_speed(
    input_filename,
    output_dir="uploads/videos",
    conf=0.5,
    max_det=200,
    device=0,
    line_color=(0, 0, 255),
    box_color=(0, 255, 0)
):
    # Lấy đường dẫn video từ MySQL
    video_path = get_video_path(input_filename)
    if not video_path or not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found at: {video_path}")

    # Tải mô hình YOLO
    model = YOLO('runs/detect/train23/weights/best.pt')  # Thay bằng đường dẫn mô hình của bạn
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video at: {video_path}")

    w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    if w == 0 or h == 0 or fps == 0:
        cap.release()
        raise ValueError("Invalid video info (width, height, or FPS).")

    # Tạo video output
    output_filename = generate_output_filename(input_filename)
    output_path = os.path.join(output_dir, output_filename)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # Thiết lập đối tượng đo tốc độ từ ultralytics.solutions
    names = {0: "car", 1: "motorcycle", 2: "truck", 3: "bus"}
    lines = [(0, h//2), (w, h//2)]  # Vạch đo tốc độ nằm giữa video
    
    speed_obj = speed_estimation.SpeedEstimator()
    speed_obj.set_args(
        reg_pts=lines,
        names=names,
        view_img=True,
    )
# Thêm hàm vẽ vạch đo tốc độ


    # Biến theo dõi đếm xe
    class_counts = {class_name: 0 for class_name in names.values()}
    tracked_ids = set()  # Lưu các ID đã được đếm
    speeds = []  # Lưu tốc độ của các xe
    
    frame_count = 0
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1

        # Theo dõi phương tiện với các lớp: 0 (car), 1 (motorcycle), 2 (truck), 3 (bus)
        tracks = model.track(frame, persist=True, conf=conf, device=device, classes=[0, 1, 2, 3], max_det=max_det)
        
        # Đếm xe theo class
        if tracks[0].boxes is not None and tracks[0].boxes.id is not None:
            boxes = tracks[0].boxes
            for box_id, cls in zip(boxes.id.int().cpu().tolist(), boxes.cls.int().cpu().tolist()):
                if box_id not in tracked_ids:  # Chỉ đếm mỗi ID một lần
                    class_name = names[cls]
                    class_counts[class_name] += 1
                    tracked_ids.add(box_id)
        
        # Hiển thị số lượng lên video
        y_pos = 30 #Khởi tạo vị trí y ban đầu để hiển thị text
        for class_name, count in class_counts.items():
            cv2.putText(frame, f"{class_name}: {count}", 
                      (w - 200, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                      0.7, (0, 255, 255), 2)
            y_pos += 30

        # Sử dụng SpeedEstimator để ước tính tốc độ và vẽ lên khung hình
        processed_frame = speed_obj.estimate_speed(frame, tracks)
        
        # Lấy thông tin tốc độ từ speed_obj nếu có
        # frame_speeds = list(speed_obj.spd.values())
        # speeds.extend(frame_speeds)
        video_writer.write(processed_frame)

    cap.release()
    video_writer.release()

    # Tính kết quả
    total_vehicles = sum(class_counts.values())
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    duration_sec = frame_count / fps if frame_count > 0 else 1

    return {
        "total_vehicles": total_vehicles,
        "avg_speed": avg_speed,
        "current_flow": total_vehicles * 3600 / duration_sec,
        "vehicle_types": {
            "car": class_counts.get("car", 0),
            "motorcycle": class_counts.get("motorcycle", 0),
            "truck": class_counts.get("truck", 0),
            "bus": class_counts.get("bus", 0)
        },
        "output_video": output_filename
    }

if __name__ == '__main__':
    vehicle_count_and_speed("test.mp4")