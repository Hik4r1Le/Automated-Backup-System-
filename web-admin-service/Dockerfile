# Sử dụng base image Python nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Thiết lập biến môi trường để Flask chạy ở chế độ Production (không debug)
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Sao chép file requirements và cài đặt dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn (app.py, templates/, static/)
COPY . .

# Mở cổng mà Flask đang chạy (8080)
EXPOSE 8080

# Lệnh khởi động server
# Flask được chạy bằng Gunicorn (môi trường production) để ổn định hơn
# Nếu chưa cài Gunicorn, bạn có thể chạy: CMD ["python", "app.py"] 
# (Nhưng Gunicorn tốt hơn cho triển khai)
CMD ["python3", "app.py"]
