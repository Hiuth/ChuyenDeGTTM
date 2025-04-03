# /ultralytics/applications/vehicle_count_and_speed.py

import cv2
from ultralytics import YOLO
from ultralytics.solutions import speed_estimation
import numpy as np
import time
import os
import warnings

# Tắt cảnh báo FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

def vehicle_count_and_speed(
    weights='runs/detect/train23/weights/best.pt',
    video_path='path/to/your/video.mp4',
    output_video_path='vehicle_count_speed_output16.mp4',
    line_points=None,
    conf=0.5,
    max_det=200,
    device=0,
    line_color=(0, 0, 255),  # Màu xanh dương
    box_color=(0, 255, 0),   # Màu xanh lá
    line_thickness=2
):
    # Kiểm tra đường dẫn weights
    if not os.path.exists(weights):
        raise FileNotFoundError(f"File mô hình không tồn tại tại: {weights}")

    # Kiểm tra đường dẫn video
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"File video không tồn tại tại: {video_path}")

    # Tải mô hình YOLO
    model = YOLO(weights)
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Không thể mở file video tại: {video_path}")

    w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
    if w == 0 or h == 0 or fps == 0:
        cap.release()
        raise ValueError("Không thể lấy thông tin video (width, height, hoặc FPS). Video có thể bị hỏng.")

    print(f"Thông tin video: width={w}, height={h}, fps={fps}")

    video_writer = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    # Định nghĩa hai vạch ngang tạo vùng đo tốc độ
    if line_points is None:
        line_top = [(0, 200), (w, 200)]    # Vạch trên
        line_bottom = [(0, h - 50), (w, h - 50)]  # Vạch dưới gần mép

    # Khởi tạo SpeedEstimator với vạch trên
    speed_estimator = speed_estimation.SpeedEstimator()
    speed_estimator.set_args(
        reg_pts=line_top,  # Sử dụng vạch trên làm vạch chính
        names=model.names,
        view_img=False,
        line_thickness=line_thickness
    )

    frame_count = 0
    class_counts = {}  # Đếm tổng số xe
    tracked_status = {}  # Theo dõi trạng thái của mỗi track_id
    prev_positions = {}  # Lưu vị trí trung điểm trước đó
    speed_status = {}   # Theo dõi trạng thái đo tốc độ
    entry_times = {}    # Lưu thời gian xe đi vào vùng
    entry_positions = {} # Lưu vị trí x khi đi vào vùng

    # Cải thiện tính toán khoảng cách thực tế
    real_distance_m = 50.0  # Khoảng cách thực tế giữa hai vạch (từ y=200 đến y=h-50, với h=768)
    pixel_distance = h - 50 - 200  # Khoảng cách pixel giữa hai vạch
    pixel_to_meter = real_distance_m / pixel_distance if pixel_distance > 0 else 1  

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Đã xử lý xong video hoặc khung hình trống.")
            break

        if frame is None or not isinstance(frame, np.ndarray):
            print(f"Khung hình không hợp lệ tại frame {frame_count}: {frame}")
            continue

        frame = np.asarray(frame, dtype=np.uint8)
        if frame.size == 0:
            print(f"Khung hình rỗng tại frame {frame_count}")
            continue

        frame_count += 1
        timestamp = frame_count / fps

        # Vẽ hai vạch ngang tạo vùng đo tốc độ
        cv2.line(frame, line_top[0], line_top[1], line_color, line_thickness)      # Vạch trên
        cv2.line(frame, line_bottom[0], line_bottom[1], (255, 0, 0), line_thickness)  # Vạch dưới

        # Theo dõi phương tiện, chỉ với lớp 0, 1, 2
        tracks = model.track(frame, persist=True, conf=conf, device=device, classes=[0, 1, 2], max_det=max_det)

        if tracks[0].boxes is not None and len(tracks[0].boxes) > 0 and tracks[0].boxes.id is not None:
            track_ids = tracks[0].boxes.id.int().cpu().tolist()
            for track_id, box in zip(track_ids, tracks[0].boxes.xyxy):
                x1, y1, x2, y2 = map(int, box)
                class_id = int(tracks[0].boxes.cls[track_ids.index(track_id)])
                class_name = model.names[class_id]

                # Vẽ bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, line_thickness)

                # Tính tốc độ
                frame = speed_estimator.estimate_speed(frame, tracks)

                # Lấy trung điểm hiện tại
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                region_top_y = line_top[0][1]    # y của vạch trên
                region_bottom_y = line_bottom[0][1]  # y của vạch dưới

                # Debug: In vị trí và ID của từng xe
                print(f"Track ID {track_id} - {class_name}: ({center_x}, {center_y})")

                if track_id not in prev_positions:
                    prev_positions[track_id] = (center_x, center_y)
                    if track_id not in speed_status:
                        speed_status[track_id] = False  # Ban đầu không đo tốc độ
                    if track_id not in entry_times:
                        entry_times[track_id] = None
                    if track_id not in entry_positions:
                        entry_positions[track_id] = None
                    continue

                prev_x, prev_y = prev_positions[track_id]
                moving_left = prev_x > center_x
                moving_right = prev_x < center_x
                direction_up = prev_y > center_y
                direction_down = prev_y < center_y

                if track_id not in tracked_status:
                    tracked_status[track_id] = False

                # Đếm khi qua vùng (giữa hai vạch)
                if not tracked_status[track_id] and region_top_y < center_y < region_bottom_y:
                    tracked_status[track_id] = True
                    if class_name not in class_counts:
                        class_counts[class_name] = set()
                    class_counts[class_name].add(track_id)

                # Đo tốc độ khi đi qua vạch trên và tiếp tục đến vạch dưới
                if region_top_y < center_y and entry_times[track_id] is None:
                    entry_times[track_id] = timestamp
                    entry_positions[track_id] = center_x
                elif region_bottom_y > center_y and entry_times[track_id] is not None:
                    exit_time = timestamp
                    entry_time = entry_times[track_id]
                    if exit_time > entry_time:  # Tránh chia cho 0
                        time_diff_sec = exit_time - entry_time
                        dist_pixel = abs(center_x - entry_positions[track_id])  # Khoảng cách pixel theo x
                        speed_pixel_per_sec = dist_pixel / time_diff_sec if time_diff_sec > 0 else 0
                        speed_m_per_sec = speed_pixel_per_sec * pixel_to_meter
                        speed_km_h = speed_m_per_sec * 3.6 if speed_m_per_sec > 0 else 0

                        # Hiển thị tốc độ trên bounding box khi trong vùng, màu đỏ
                        if region_top_y < center_y < region_bottom_y:
                            cv2.putText(frame, f"{speed_km_h:.1f} km/h", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  # Màu đỏ
                            print(f"Track ID {track_id} - {class_name}: {speed_km_h:.2f} km/h")
                    entry_times[track_id] = None  # Đặt lại sau khi ra khỏi vùng

                prev_positions[track_id] = (center_x, center_y)

        # Hiển thị số lượng xe đã đếm
        if class_counts:
            y_pos = 30
            for class_name, track_ids in class_counts.items():
                label = f"{class_name}: {len(track_ids)}"
                cv2.putText(frame, label, (w - 200, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                y_pos += 30

        video_writer.write(frame)

    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    vehicle_count_and_speed(
        video_path='C:/Users/hiuth/Downloads/traffic_video.avi',
        line_color=(0, 0, 255),
        box_color=(0, 255, 0)
    )