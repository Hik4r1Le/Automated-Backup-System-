# storage_client.py (ĐÃ SỬA ĐỔI)
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime # Thêm import này

# Tải các biến môi trường từ file .env (nếu có)
load_dotenv()

class StorageClient:
    """Class xử lý giao tiếp với S3-compatible storage (MinIO)."""
    
    def __init__(self, endpoint, access_key, secret_key, bucket_name):
        self.bucket_name = bucket_name
        self.endpoint = endpoint
        
        # 1. Khởi tạo S3 Client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
    def ensure_bucket_exists(self, logger=None):
        # ... (Hàm này giữ nguyên)
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            if logger:
                logger.log_system_event(f"Bucket '{self.bucket_name}' already exists.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    if logger:
                        logger.log_system_event(f"Bucket '{self.bucket_name}' created successfully.", "WARNING")
                except ClientError as ce:
                    if logger:
                        logger.log_system_event(f"Error creating bucket '{self.bucket_name}': {ce}", "ERROR")
                    raise
            else:
                if logger:
                    logger.log_system_event(f"Error checking bucket '{self.bucket_name}': {e}", "ERROR")
                raise

    def upload(self, file_path: str):
        """Upload file từ đường dẫn cục bộ lên MinIO, sử dụng Versioning Key."""
        
        file_name = os.path.basename(file_path)
        base, ext = os.path.splitext(file_name)
        
        # Tạo Unique Versioning Key: filename_YYYYMMDD_HHmmss.ext
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned_key = f"{base}_{timestamp}{ext}" # Key S3 mới

        with open(file_path, "rb") as f:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=versioned_key, # SỬ DỤNG KEY CÓ VERSION
                Body=f
            )
        
        return {
            'destination': f"s3://{self.bucket_name}/{versioned_key}",
            'filename': file_name,
            'versioned_key': versioned_key # Trả về key mới
        }

# Hàm tiện ích để tạo client từ biến môi trường (Giữ nguyên)
def create_client_from_env():
    return StorageClient(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        bucket_name=os.getenv("MINIO_BUCKET")
    )
