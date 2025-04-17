// script.js
document.addEventListener('DOMContentLoaded', () => {
    const videoUpload = document.getElementById('video-upload');
    const uploadButton = document.querySelector('.upload-button');
    const analyzeButton = document.getElementById('analyze-button');
    const downloadLink = document.getElementById('download-link');
    const videoPlayer = document.getElementById('traffic-video');
    const videoStatus = document.getElementById('video-status');
    const progressStatus = document.querySelector('.progress-status');
    const totalVehicles = document.getElementById('total-vehicles');
    const avgSpeed = document.getElementById('avg-speed');
    const currentFlow = document.getElementById('current-flow');
    const analysisStatus = document.getElementById('analysis-status');
    const motorbikeCount = document.getElementById('motorbike-count');
    const carCount = document.getElementById('car-count');
    const truckCount = document.getElementById('truck-count');
    const busCount = document.getElementById('bus-count');

    uploadButton.addEventListener('click', () => videoUpload.click());

    videoUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            videoStatus.textContent = `Đã chọn: ${file.name}`;
            progressStatus.textContent = 'Sẵn sàng phân tích';
            analyzeButton.disabled = false;

            const videoURL = URL.createObjectURL(file);
            const source = videoPlayer.querySelector('source');
            source.src = videoURL;
            videoPlayer.load();
            videoPlayer.onloadeddata = () => {
                videoPlayer.style.display = 'block';
                document.querySelector('.video-placeholder').style.display = 'none';
                videoPlayer.play().catch(error => console.log('Auto play failed:', error));
            };
        }
    });

    analyzeButton.addEventListener('click', () => {
        const file = videoUpload.files[0];
        if (!file) {
            alert('Vui lòng chọn video trước!');
            return;
        }

        analyzeButton.disabled = true;
        progressStatus.textContent = 'Đang upload và phân tích...';
        analysisStatus.textContent = 'Đang xử lý';

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
                downloadLink.href = `/download?fileName=${encodeURIComponent(filename)}`;
                downloadLink.download = data.results.output_video;
                downloadLink.style.display = 'inline-block';
                alert('Phân tích hoàn tất! Bạn có thể tải video đã xử lý.');
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
            alert(`Lỗi: ${error.message}`);
        })
        .finally(() => {
            analyzeButton.disabled = false;
        });
    });

    document.querySelector('.alert-button').addEventListener('click', () => {
        alert('Hệ thống đang trong giai đoạn thử nghiệm. Vui lòng sử dụng cẩn thận và báo cáo lỗi nếu có.');
    });
});