# vehicle_count_and_speed.py
import cv2
from ultralytics import YOLO
import numpy as np
import os
import uuid
from datetime import datetime
from database import get_video_path

def pixel_to_meter_at_y(y_position, frame_height, real_distance_m, pixel_distance):
    base_ratio = real_distance_m / pixel_distance
    perspective_factor = 1 + ((frame_height - y_position) / frame_height) * 1.5
    return base_ratio * perspective_factor

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

    # Vùng đo tốc độ
    line_top = [(0, int(h * 0.5)), (w, int(h * 0.5))]
    line_bottom = [(0, int(h * 0.8)), (w, int(h * 0.8))]
    real_distance_m = 50.0  # Khoảng cách thực tế giữa hai vạch (m)
    pixel_distance = line_bottom[0][1] - line_top[0][1]

    # Biến theo dõi
    frame_count = 0
    class_counts = {}  # Lưu số lượng từng loại xe theo track_id
    tracked_status = {}  # Trạng thái đã đếm của mỗi track_id
    prev_positions = {}  # Vị trí trước đó
    entry_times = {}     # Thời gian vào vùng
    entry_positions = {} # Vị trí x vào vùng
    speed_history = {}   # Lịch sử tốc độ
    filtered_speeds = {} # Tốc độ đã làm mịn
    SMOOTH_FACTOR = 8
    ALPHA = 0.2

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_count += 1
        timestamp = frame_count / fps

        # Vẽ vạch
        cv2.line(frame, line_top[0], line_top[1], line_color, 2)
        cv2.line(frame, line_bottom[0], line_bottom[1], (255, 0, 0), 2)

        # Theo dõi phương tiện với các lớp: 0 (car), 1 (motorcycle), 3 (truck), 4 (bus)
        tracks = model.track(frame, persist=True, conf=conf, device=device, classes=[0, 1, 3, 4], max_det=max_det)
        if tracks[0].boxes is not None and tracks[0].boxes.id is not None:
            track_ids = tracks[0].boxes.id.int().cpu().tolist()
            for track_id, box in zip(track_ids, tracks[0].boxes.xyxy):
                x1, y1, x2, y2 = map(int, box)
                class_id = int(tracks[0].boxes.cls[track_ids.index(track_id)])
                
                # Gán tên lớp theo class_id
                class_name = {0: "car", 1: "motorcycle", 2: "truck", 3: "bus"}.get(class_id, "unknown")

                # Vẽ bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

                # Tính trung điểm
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # Đếm xe
                if track_id not in tracked_status:
                    tracked_status[track_id] = False
                if not tracked_status[track_id] and line_top[0][1] < center_y < line_bottom[0][1]:
                    tracked_status[track_id] = True
                    if class_name not in class_counts:
                        class_counts[class_name] = set()
                    class_counts[class_name].add(track_id)

                # Đo tốc độ
                if track_id not in prev_positions:
                    prev_positions[track_id] = (center_x, center_y)
                    entry_times[track_id] = None
                    entry_positions[track_id] = None
                    continue

                prev_x, prev_y = prev_positions[track_id]
                if line_top[0][1] < center_y and entry_times[track_id] is None:
                    entry_times[track_id] = timestamp
                    entry_positions[track_id] = center_x
                elif line_bottom[0][1] > center_y and entry_times[track_id] is not None:
                    exit_time = timestamp
                    entry_time = entry_times[track_id]
                    if exit_time > entry_time:
                        time_diff = exit_time - entry_time
                        dist_pixel = abs(center_x - entry_positions[track_id])
                        speed_pixel_per_sec = dist_pixel / time_diff if time_diff > 0 else 0
                        current_pixel_to_meter = pixel_to_meter_at_y(center_y, h, real_distance_m, pixel_distance)
                        speed_m_per_sec = speed_pixel_per_sec * current_pixel_to_meter
                        speed_km_h = speed_m_per_sec * 3.6

                        if track_id not in speed_history:
                            speed_history[track_id] = []
                            filtered_speeds[track_id] = 0
                        speed_history[track_id].append(speed_km_h)
                        if len(speed_history[track_id]) > SMOOTH_FACTOR:
                            speed_history[track_id].pop(0)
                        current_avg = sum(speed_history[track_id]) / len(speed_history[track_id])
                        filtered_speeds[track_id] = ALPHA * current_avg + (1 - ALPHA) * filtered_speeds[track_id]

                        cv2.putText(frame, f"{filtered_speeds[track_id]:.1f} km/h", 
                                    (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

                prev_positions[track_id] = (center_x, center_y)

        # Hiển thị số lượng xe trên frame
        y_pos = 30
        for class_name, track_ids in class_counts.items():
            cv2.putText(frame, f"{class_name}: {len(track_ids)}", 
                        (w - 200, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            y_pos += 30

        video_writer.write(frame)

    cap.release()
    video_writer.release()

    # Tính kết quả
    total_speed = sum(filtered_speeds.values()) if filtered_speeds else 0
    avg_speed = total_speed / len(filtered_speeds) if filtered_speeds else 0
    total_vehicles = sum(len(ids) for ids in class_counts.values())
    duration_sec = frame_count / fps if frame_count > 0 else 1

    # Tổng số từng loại xe
    car_count = len(class_counts.get("car", set()))
    motorcycle_count = len(class_counts.get("motorcycle", set()))
    truck_count = len(class_counts.get("truck", set()))
    bus_count = len(class_counts.get("bus", set()))

    return {
        "total_vehicles": total_vehicles,
        "avg_speed": avg_speed,
        "current_flow": total_vehicles * 3600 / duration_sec,
        "vehicle_types": {
            "car": car_count,
            "motorcycle": motorcycle_count,
            "truck": truck_count,
            "bus": bus_count
        },
        "output_video": output_filename
    }

if __name__ == '__main__':
     vehicle_count_and_speed("test.mp4")