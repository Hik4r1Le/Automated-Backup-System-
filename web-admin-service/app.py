import os
import json
import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS 
from s3_backend_client import s3_client # Import S3 Client mới

app = Flask(__name__)
CORS(app) 

# Đường dẫn thư mục NGUỒN (Phải khớp với HostPath mountPath trong K8s YAML)
SOURCE_DIR = os.getenv("WATCH_DIR", "/mnt/source")

# Hằng số cho cơ chế Restore Tạm thời
RESTORE_TEMP_SUFFIX = ".RESTORE_TEMP"

# Đảm bảo thư mục tồn tại khi Flask khởi động
os.makedirs(SOURCE_DIR, exist_ok=True)

# ----------------------------------------------------
# ENDPOINTS CŨ (CRUD File Nguồn)
# ----------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        files = [f for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
        # Loại bỏ các file tạm đang trong quá trình restore
        files = [f for f in files if not f.endswith(RESTORE_TEMP_SUFFIX)] 
        return jsonify({'files': sorted(files)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<filename>', methods=['GET'])
def read_file(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        return jsonify({'filename': filename, 'content': content}), 200
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<filename>', methods=['PUT', 'POST'])
def save_file(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    data = request.get_json()
    content = data.get('content', '')
    
    is_new = not os.path.exists(file_path)
    
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        
        message = 'File created successfully.' if is_new else 'File updated successfully.'
        return jsonify({'message': message, 'filename': filename}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<filename>', methods=['DELETE'])
def delete_file(filename):
    file_path = os.path.join(SOURCE_DIR, filename)
    try:
        os.remove(file_path)
        return jsonify({'message': f'File {filename} deleted successfully.'}), 200
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----------------------------------------------------
# ENDPOINT MỚI 1: Lấy Danh sách các Phiên bản đã Backup
# ----------------------------------------------------
@app.route('/api/backup/versions', methods=['GET'])
def list_backup_versions():
    """Lấy danh sách tất cả các phiên bản file từ MinIO."""
    try:
        versions = s3_client.list_all_versions()
        
        # Nhóm các phiên bản theo tên file gốc để dễ hiển thị trên UI
        # Logic này sẽ giúp UI hiển thị: "report.pdf (3 versions)"
        grouped_versions = {}
        for item in versions:
            # Giả sử tên file gốc không có dấu gạch dưới và ngày tháng phức tạp
            # (Nếu dùng cơ chế versioning bằng ngày giờ: filename_YYYYMMDD_HHmmss.ext)
            
            # Tên file gốc (lý tưởng là Watcher cung cấp metadata)
            # Ở đây, ta dùng key nguyên bản làm tên phiên bản
            base_name = item['key']
            
            if base_name not in grouped_versions:
                grouped_versions[base_name] = []
            
            grouped_versions[base_name].append(item)
            
        return jsonify(grouped_versions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----------------------------------------------------
# ENDPOINT MỚI 2: Khôi phục File (Sử dụng cơ chế file tạm)
# ----------------------------------------------------
@app.route('/api/backup/restore/<path:object_key>', methods=['POST'])
def restore_file(object_key):
    """
    Tải file từ MinIO về HostPath, sử dụng tên tạm thời để Watcher bỏ qua.
    'object_key' là Key S3 (ví dụ: document.pdf_20251214_133045.pdf)
    """
    
    # Lấy tên file gốc (ví dụ: document.pdf)
    # Nếu key không phải là versioning, nó chính là tên file gốc
    base_filename = os.path.basename(object_key)
    
    # 1. Định nghĩa tên file tạm thời trong HostPath
    temp_file_path = os.path.join(SOURCE_DIR, base_filename + RESTORE_TEMP_SUFFIX)
    
    try:
        # 2. Tải file từ MinIO về tên file tạm thời
        s3_client.download_file(object_key, temp_file_path)
        
        # 3. Đổi tên file tạm thời thành tên file gốc
        # Lệnh này sẽ kích hoạt sự kiện on_created hoặc on_modified cho Watcher
        final_file_path = os.path.join(SOURCE_DIR, base_filename)
        os.rename(temp_file_path, final_file_path)

        return jsonify({
            'message': f'File {base_filename} restored successfully from backup key {object_key}.',
            'filename': base_filename
        }), 200
        
    except Exception as e:
        # Đảm bảo xóa file tạm nếu có lỗi xảy ra trước khi đổi tên
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({'error': f'Restore failed for {object_key}: {e}'}), 500

if __name__ == '__main__':
    # Chạy trên cổng 8080 để dễ dàng expose trong K8s
    app.run(host='0.0.0.0', port=8080, debug=True)
