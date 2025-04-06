from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from database import get_connection, close_connection, insert_video, get_video_path, get_video_info, get_all_videos, update_processed_filename

app = Flask(__name__)

VIDEO_STORGE_PATH = '/upload/videos' # Đường dẫn lưu video gốc, nếu không có thì tạo mới
if not os.path.exists(VIDEO_STORGE_PATH):
    os.makedirs(VIDEO_STORGE_PATH)
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

def allowed_file(filename): # kiểm tra định dạng file video
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 
#'.' in filename: Đảm bảo file có dấu chấm (ví dụ: video.mp4), vì file hợp lệ thường có phần mở rộng.
#filename.rsplit('.', 1)[1].lower(): Lấy phần mở rộng của file (ví dụ: từ video.mp4 lấy mp4), chuyển thành chữ thường để so sánh.
#in ALLOWED_EXTENSIONS: Kiểm tra xem phần mở rộng có nằm trong tập hợp ALLOWED_EXTENSIONS không. Trả về True nếu hợp lệ, False nếu không.

def generate_unique_filename(orignal_Filename): # tạo tên file duy nhất để tránh trùng lặp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S") # Lấy thời gian hiện tại theo định dạng YYYYMMDDHHMMSS
    unique_id = str(uuid.uuid4())[:8] # Tạo một UUID ngẫu nhiên và lấy 8 ký tự đầu tiên
    exception = os.path.splitext(orignal_Filename)[1] # Lấy phần mở rộng của file gốc, os.path.splitext(orignal_Filename): Tách tên file và phần mở rộng, trả về một tuple (name, extension).
    return f"video_{timestamp}_{unique_id}{exception}" # Trả về tên file duy nhất theo định dạng: YYYYMMDDHHMMSS_UUID.extension (ví dụ: video_20231010123456_12345678.mp4).


@app.route('/upload_and_analyze', methods=['POST']) # định nghĩa route /upload với phương thức POST
def upload_and_analyze_video(): # hàm xử lý upload video
    if'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400 # kiểm tra xem có file video trong request hay không
    file = request.files['video'] # lấy file video từ request
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'No selected file or invalid file type'}), 400
    
    #Tiến hành lưu video gốc vào thư mục VIDEO_STORAGE_PATH
    orignal_filename = secure_filename(file.filename) # Lấy tên file gốc
    new_filename = generate_unique_filename(orignal_filename) # Tạo tên file duy nhất
    file_path = os.path.join(VIDEO_STORGE_PATH, new_filename) # Tạo đường dẫn lưu file mới
    file.save(file_path) # Lưu file vào đường dẫn đã tạo
    
    #lưu thông tin video vào cơ sở dữ liệu
    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Lấy thời gian upload video
    if not insert_video(new_filename,file_path, upload_time,orignal_filename):
        return jsonify({'error': 'Failed to save video info into database'}), 500
    try:
        from vehicle_count_speed import vehicle_count_and_speed #nhập module vehicle_count_speed
        result = vehicle_count_and_speed(input_filename=new_filename, output_dir= VIDEO_STORGE_PATH) # gọi hàm vehicle_count_and_speed với đường dẫn video. Kết quả (results) chứa thông tin về video đã xử lý, bao gồm tên file đầu ra.
        if not update_processed_filename(orignal_filename, result['output_video']):
            return jsonify({'error': 'Failed to update processed filename in database'}), 500
        return jsonify({
            "message": "Video uploaded and analyzed successfully",
            "Video Title": new_filename,
            "result": result
        }),200 # trả về kết quả dưới dạng JSON với mã trạng thái 200 (thành công)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/download', methods=['GET']) # định nghĩa route /videos với phương thức GET
def download_video():
    fileName= request.args.get('fileName') # lấy tên file từ tham số truy vấn
    if not fileName:
        return jsonify({'error': 'No file name provided'}), 400
    
    video = get_video_info(fileName)
    if not video or not video['processed_Filename']:
        return jsonify({'error': 'Processed video not found'}), 404
    
    proccessed_video_path = os.path.join(VIDEO_STORGE_PATH, video['processed_Filename']) # tạo đường dẫn đến video đã xử lý
    if not os.path.exists(proccessed_video_path):
        return jsonify({'error': 'Processed video file does not exist'}), 404
    return send_file(proccessed_video_path, as_attachment=True, download_video_name=video['processed_Filename'],mimetype='video.mp4') # gửi file video đã xử lý về cho client với tên file đã xử lý

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)