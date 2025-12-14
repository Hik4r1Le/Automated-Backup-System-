# s3_backend_client.py
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Tải các biến môi trường
load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://storage-service:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "ceph-backup-bucket")

class S3BackendClient:
    """Xử lý các thao tác S3 (MinIO) cho Web Admin API."""

    def __init__(self):
        self.bucket = MINIO_BUCKET
        self.s3_client = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY
        )

    def list_all_versions(self):
        """Liệt kê tất cả các đối tượng (versions) trong bucket MinIO."""
        try:
            # Sử dụng list_objects_v2 để lấy danh sách object
            response = self.s3_client.list_objects_v2(Bucket=self.bucket)
            
            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({
                        'key': obj['Key'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'size': obj['Size']
                    })
            return objects
        except ClientError as e:
            raise Exception(f"S3 Error listing objects: {e}")
        except Exception as e:
            raise Exception(f"Error connecting to MinIO: {e}")

    def download_file(self, object_key, destination_path):
        """Tải file từ MinIO về đường dẫn cục bộ."""
        try:
            self.s3_client.download_file(
                Bucket=self.bucket,
                Key=object_key,
                Filename=destination_path
            )
            return True
        except ClientError as e:
            raise Exception(f"S3 Error downloading {object_key}: {e}")
        except Exception as e:
            raise Exception(f"General error during download: {e}")

# Khởi tạo client MinIO cho Web Admin
s3_client = S3BackendClient()
