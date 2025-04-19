
document.addEventListener('DOMContentLoaded', () => {
    const videoUpload = document.getElementById('video-upload');
    const uploadButton = document.querySelector('.upload-button');
    const analyzeButton = document.getElementById('analyze-button');
    const downloadButton = document.getElementById('download-button');
    const videoPlayer = document.getElementById('traffic-video');
    const videoStatus = document.getElementById('video-status');
    const progressStatus = document.querySelector('.progress-status');
    const totalVehicles = document.getElementById('total-vehicles');
    const analysisStatus = document.getElementById('analysis-status');
    const motorbikeCount = document.getElementById('motorbike-count');
    const carCount = document.getElementById('car-count');
    const truckCount = document.getElementById('truck-count');
    const busCount = document.getElementById('bus-count');
    const loadingOverlay = document.getElementById('loading-overlay');
    const errorMessage = document.getElementById('error-message');
    const alertButton = document.querySelector('.alert-button');
    const alertModal = document.getElementById('alert-modal');
    const closeModal = document.querySelector('.close-modal');

    let downloadUrl = ''; // Biến lưu URL tải xuống

    // Hiển thị thông báo lỗi tạm thời
    const showErrorMessage = (message) => {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 3000); // Ẩn sau 3 giây
    };

    // Kiểm tra kích thước file (tối đa 500MB)
    const isFileSizeValid = (file) => {
        const maxSizeInBytes = 500 * 1024 * 1024; // 500MB
        return file.size <= maxSizeInBytes;
    };

    // Sửa lỗi chọn file: Gắn sự kiện trực tiếp vào uploadButton
    uploadButton.addEventListener('click', () => {
        videoUpload.click();
    });

    videoUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            // Kiểm tra kích thước file
            if (!isFileSizeValid(file)) {
                showErrorMessage('Kích thước video vượt quá 500MB. Vui lòng chọn video nhỏ hơn.');
                videoUpload.value = ''; // Xóa file đã chọn
                return;
            }

            videoStatus.textContent = `Đã chọn: ${file.name}`;
            progressStatus.textContent = 'Sẵn sàng phân tích';
            analyzeButton.disabled = false;

            // Thử hiển thị video
            const videoURL = URL.createObjectURL(file);
            const source = videoPlayer.querySelector('source');
            source.src = videoURL;
            videoPlayer.load();

            // Luôn hiển thị thẻ video sau khi chọn file
            videoPlayer.style.display = 'block';
            document.querySelector('.video-placeholder').style.display = 'none';

            // Xử lý lỗi nếu video không hiển thị được
            videoPlayer.onerror = () => {
                showErrorMessage('Trình duyệt không thể hiển thị video này, nhưng bạn vẫn có thể phân tích.');
                videoPlayer.style.display = 'none';
                document.querySelector('.video-placeholder').style.display = 'flex';
                // Không xóa file đã chọn, vẫn cho phép phân tích
            };
        }
    });

    analyzeButton.addEventListener('click', () => {
        const file = videoUpload.files[0];
        if (!file) {
            showErrorMessage('Vui lòng chọn video trước!');
            return;
        }

        analyzeButton.disabled = true;
        progressStatus.textContent = 'Đang upload và phân tích...';
        analysisStatus.textContent = 'Đang xử lý';

        // Hiển thị overlay loading
        loadingOverlay.style.display = 'flex';

        const formData = new FormData();
        formData.append('video', file);
        console.log('Bắt đầu gửi yêu cầu fetch...', new Date().toISOString());
        console.log('FormData entries:', Array.from(formData.entries()));
        console.log('Origin:', window.location.origin);

        fetch('http://127.0.0.1:5000/upload_and_analyze', {
            method: 'POST',
            body: formData,
            mode: 'cors',
            credentials: 'include'
        })
        .then(response => {
            console.log('Nhận phản hồi, status:', response.status, new Date().toISOString());
            console.log('Response headers:', Object.fromEntries(response.headers));
            if (!response.ok) {
                throw new Error(`Lỗi HTTP! Status: ${response.status}`);
            }
            return response.text();
        })
        .then(text => {
            console.log('Response text:', text, new Date().toISOString());
            let data;
            try {
                data = JSON.parse(text);
                console.log('Parsed JSON data:', data);
            } catch (jsonError) {
                throw new Error(`Lỗi phân tích JSON: ${jsonError.message}`);
            }
            if (data.error) throw new Error(data.error);

            videoStatus.textContent = `Đã xử lý: ${data.Video_Title || data.filename || 'video'}`;
            progressStatus.textContent = 'Phân tích hoàn tất';
            analysisStatus.textContent = 'Đã phân tích';

            totalVehicles.textContent = data.results.total_vehicles || '--';
            // avgSpeed.textContent = (data.results.avg_speed || 0).toFixed(1) || '--';
            // currentFlow.textContent = (data.results.current_flow || 0).toFixed(0) || '--';

            const vehicleTypes = data.results.vehicle_types || {};
            motorbikeCount.textContent = vehicleTypes.motorcycle || '0';
            carCount.textContent = vehicleTypes.car || '0';
            truckCount.textContent = vehicleTypes.truck || '0';
            busCount.textContent = vehicleTypes.bus || '0';

            if (data.results.output_video) {
                const filename = data["Video Title"];
                if (!filename) {
                    throw new Error('Filename is undefined');
                }
                downloadUrl = `/download?fileName=${encodeURIComponent(filename)}`;
                downloadButton.disabled = false; // Bật nút tải xuống khi có video từ server
            }
        })
        .catch(error => {
            console.error('Upload thất bại:', error.message, new Date().toISOString());
            console.error('Stack trace:', error.stack);
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                console.error('Lỗi mạng hoặc CORS, kiểm tra server hoặc cấu hình CORS');
            } else if (error.name === 'SyntaxError') {
                console.error('Lỗi phân tích JSON');
            }
            progressStatus.textContent = 'Lỗi khi xử lý';
            analysisStatus.textContent = 'Lỗi';
            showErrorMessage(`Lỗi: ${error.message}`);
        })
        .finally(() => {
            // Ẩn overlay loading khi phân tích hoàn tất hoặc có lỗi
            loadingOverlay.style.display = 'none';
            analyzeButton.disabled = false;
        });
    });

    // Xử lý sự kiện tải xuống
    downloadButton.addEventListener('click', () => {
        if (downloadUrl) {
            window.location.href = downloadUrl; // Tải file khi nhấn nút
        }
    });

    // Xử lý sự kiện mở/đóng modal
    alertButton.addEventListener('click', () => {
        alertModal.style.display = 'flex';
    });

    closeModal.addEventListener('click', () => {
        alertModal.style.display = 'none';
    });

    // Đóng modal khi nhấp ra ngoài
    window.addEventListener('click', (e) => {
        if (e.target === alertModal) {
            alertModal.style.display = 'none';
        }
    });
});