import cv2
from ultralytics import YOLO
from ultralytics.solutions import speed_estimation

# Khởi tạo video và mô hình
cap = cv2.VideoCapture("traffic_video.avi")
assert cap.isOpened(), "Lỗi khi đọc tệp video"
model = YOLO("runs/detect/train23/weights/best.pt")
names = {0: "car", 1: "motorcycle", 2: "truck", 3: "bus"}

# Khởi tạo đếm lớp và ID đã theo dõi
class_counts = {class_name: 0 for class_name in names.values()}
tracked_ids = set()  # Lưu các ID đã được đếm

# Thiết lập ghi video
w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))
video_writer = cv2.VideoWriter("speed_management.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

# Điểm vùng tính tốc độ
lines = [(0, h // 2), (w, h // 2)]

# Khởi tạo SpeedEstimator
speed_obj = speed_estimation.SpeedEstimator()
speed_obj.set_args(
    reg_pts=lines,  # Điểm vùng tính tốc độ
    names=names,    # Tên lớp
    view_img=True   # Hiển thị video đầu ra
)

# Mảng lưu tốc độ
vehicle_speeds = []

# Xử lý video
while cap.isOpened():
    success, im0 = cap.read()
    if not success:
        break

    tracks = model.track(im0, persist=True, show=False)

    # Đếm phương tiện theo lớp
    if tracks[0].boxes is not None and tracks[0].boxes.id is not None:
        boxes = tracks[0].boxes
        for box_id, cls in zip(boxes.id.int().cpu().tolist(), boxes.cls.int().cpu().tolist()):
            if box_id not in tracked_ids:  # Chỉ đếm mỗi ID một lần
                class_name = names[cls]
                class_counts[class_name] += 1
                tracked_ids.add(box_id)

        # Hiển thị số lượng lên video
        y_pos = 30
        for class_name, count in class_counts.items():
            cv2.putText(im0, f"{class_name}: {count}",
                        (w - 500, y_pos), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (0, 255, 255), 2)
            y_pos += 30

    # Ước lượng tốc độ
    im0 = speed_obj.estimate_speed(im0, tracks)

    # Lấy tốc độ từ tracks
    for track in tracks:
        if hasattr(track, 'speed') and track.speed is not None:
            for box in track.boxes:
                track_id = int(box.id) if box.id is not None else None
                if track_id:
                    speed = track.speed
                    vehicle_speeds.append(speed)
                    print(f"Phương tiện ID {track_id}: {speed:.2f} m/s")

    video_writer.write(im0)

# In kết quả cuối cùng
print("\nKết quả đếm xe:")
for class_name, count in class_counts.items():
    print(f"{class_name}: {count}")
if vehicle_speeds:
    print(f"Tốc độ trung bình: {sum(vehicle_speeds) / len(vehicle_speeds):.2f} m/s")
else:
    print("Không ghi nhận tốc độ.")

# In tất cả tốc độ
print("Danh sách tốc độ:", [f"{speed:.2f} m/s" for speed in vehicle_speeds])

cap.release()
video_writer.release()
cv2.destroyAllWindows()