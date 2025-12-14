import os
import time
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from botocore.exceptions import ClientError

# Thiết lập đường dẫn để import logging module (Điều chỉnh nếu cần)
sys.path.insert(0, str(Path(__file__).parent.parent / "logging-module"))
from backup_logger import get_logger
from storage_client import create_client_from_env

# Hằng số cho cơ chế Restore Tạm thời (PHẢI KHỚP VỚI WEB ADMIN)
RESTORE_TEMP_SUFFIX = ".RESTORE_TEMP"

# Lấy các biến môi trường từ môi trường triển khai K8s
WATCH_DIR = os.getenv("WATCH_DIR", "/mnt/source")
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "ceph-backup-bucket")

# ----------------------------------------------------
# Lớp 1: Xử lý sự kiện (Tích hợp logic Trì hoãn & Restore)
# ----------------------------------------------------
class BackupEventHandler(FileSystemEventHandler):
    """Xử lý sự kiện tạo và sửa đổi file, kích hoạt backup và ghi log."""
    
    def __init__(self, storage_client, logger):
        self.storage_client = storage_client
        self.logger = logger
        self._last_modified = {}  
        self._created_files = {}  # Lưu trữ file mới tạo, chờ on_modified đầu tiên
        self._CREATION_SKIP_TIME = 2 # Giây: Thời gian tối đa file được coi là 'mới tạo'

    def _should_skip_file(self, file_path):
        """Kiểm tra xem file có phải là file tạm thời hoặc file mới tạo chưa ghi nội dung không."""
        
        # BỎ QUA 1: File tạm thời đang được Web Admin Restore
        if file_path.endswith(RESTORE_TEMP_SUFFIX):
            self.logger.log_system_event(
                f"Skipping temporary file during Restore: {file_path}", 
                "DEBUG"
            )
            return True
        
        # BỎ QUA 2: File mới được tạo gần đây và đang chờ sự kiện modified đầu tiên
        if file_path in self._created_files:
            # Nếu file quá cũ, có thể đã bị bỏ lỡ sự kiện modified, ta vẫn backup
            if time.time() - self._created_files[file_path] > self._CREATION_SKIP_TIME:
                self.logger.log_system_event(f"File {file_path} created but no modification seen. Forcing backup.", "WARNING")
                del self._created_files[file_path] # Xóa cờ và cho phép backup
                return False 
            
            # Nếu file còn mới, skip backup và chờ modified
            self.logger.log_system_event(f"Skipping initial created event for {file_path}. Waiting for modification.", "DEBUG")
            return True
            
        return False

    def on_created(self, event):
        if not event.is_directory:
            # GHI NHẬN: Lưu file vào danh sách chờ và bỏ qua backup
            self._created_files[event.src_path] = time.time()
            self.logger.log_file_detected(event.src_path, "initial create (skipped)")
            # KHÔNG GỌI backup_file

    def on_modified(self, event):
        if not event.is_directory:
            file_path = event.src_path
            
            # 1. Kiểm tra Restore/Trì hoãn (Skip logic)
            # Hàm này kiểm tra file tạm, file mới tạo đang chờ và quyết định có nên skip không
            if self._should_skip_file(file_path):
                return 

            # 2. Xử lý file mới tạo (nếu nó vừa vượt qua _should_skip_file)
            is_newly_created = file_path in self._created_files
            if is_newly_created:
                del self._created_files[file_path] # Xóa cờ, cho phép backup

            # 3. Kiểm tra Trùng lặp (Debounce)
            # Chỉ kiểm tra debounce nếu đây KHÔNG phải là sự kiện modified đầu tiên sau created
            if file_path in self._last_modified and time.time() - self._last_modified[file_path] < 1:
                if not is_newly_created:
                    return # Bỏ qua nếu là sự kiện trùng lặp
                
            self._last_modified[file_path] = time.time()
            
            # 4. Ghi log và Backup
            log_type = "initial modified" if is_newly_created else "modified"
            self.logger.log_file_detected(file_path, log_type)
            
            self.backup_file(file_path)

    def on_deleted(self, event):
        # Ghi log sự kiện xóa file
        if not event.is_directory:
            self.logger.log_system_event(f"File DELETED: {event.src_path}", "WARNING")

    def backup_file(self, file_path):
        """Thực hiện backup S3 và ghi log kết quả."""
        file_path_obj = Path(file_path)
        
        try:
            # Tránh lỗi nếu file bị xóa ngay sau khi phát hiện
            if not file_path_obj.exists():
                return
            
            file_size = file_path_obj.stat().st_size
            
            # GHI LOG BẮT ĐẦU
            self.logger.log_backup_start(file_path, file_size)
            start_time = time.time()
            
            # 1. THỰC HIỆN UPLOAD TỚI MINIO (Key mới)
            response = self.storage_client.upload(file_path)
            
            duration = time.time() - start_time
            
            # GHI LOG THÀNH CÔNG (Dùng Versioned Key mới để log)
            self.logger.log_backup_success(
                file_path=file_path,
                destination=response['destination'], # Key S3 mới có timestamp
                file_size=file_size,
                duration=duration
            )
            
        except ClientError as e:
            error_msg = f"S3 Client Error: {e.response['Error']['Code']}"
            # GHI LOG THẤT BẠI
            self.logger.log_backup_failure(file_path, error_msg, file_size if 'file_size' in locals() else None)
        
        except Exception as e:
            error_msg = f"General Upload Error: {str(e)}"
            # GHI LOG THẤT BẠI
            self.logger.log_backup_failure(file_path, error_msg, file_size if 'file_size' in locals() else None)

# ----------------------------------------------------
# Lớp 2: Quản lý Watcher (Main Orchestrator)
# ----------------------------------------------------
class WatcherOrchestrator:
    def __init__(self):
        # 1. Khởi tạo Logger
        self.logger = get_logger(name="watcher_core", log_dir=LOG_DIR, log_level=LOG_LEVEL)
        
        # 2. Khởi tạo Storage Client
        self.storage_client = create_client_from_env()
        
        # 3. Kiểm tra kết nối và tạo Bucket
        try:
            self.storage_client.ensure_bucket_exists(self.logger)
            self.logger.log_system_event("MinIO connection established successfully.")
        except Exception as e:
            self.logger.log_system_event(f"CRITICAL: Failed to connect or create MinIO bucket: {e}", "CRITICAL")
            sys.exit(1)
            
        self.event_handler = BackupEventHandler(self.storage_client, self.logger)
        self.observer = Observer()
        
        self.logger.log_system_event(f"Monitoring directory: {WATCH_DIR}", "INFO")

    def run(self):
        """Thiết lập và chạy watchdog observer."""
        self.observer.schedule(self.event_handler, WATCH_DIR, recursive=False)
        self.observer.start()
        self.logger.log_system_event("Watcher Service started and running.", "INFO")

        try:
            while True:
                # Đợi 1 giây, giữ cho luồng chính hoạt động
                time.sleep(1) 
        except KeyboardInterrupt:
            self.logger.log_system_event("Interrupt received. Stopping watcher...", "WARNING")
        finally:
            self.observer.stop()
            self.observer.join()
            
            # In thống kê khi watcher dừng
            self.logger.print_stats()

if __name__ == "__main__":
    watcher = WatcherOrchestrator()
    watcher.run()
