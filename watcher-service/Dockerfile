# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Sao chép các thư mục module cần thiết
COPY ./requirements.txt .
COPY ./storage_client.py .
COPY ./watcher_service.py .
COPY ./backup_logger.py .

# Cài đặt dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Thiết lập biến môi trường để Watcher Service biết nơi Log Module được đặt
ENV PYTHONPATH=/app

# Lệnh chạy Watcher
CMD ["python3", "watcher_service.py"]
