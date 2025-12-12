#!/usr/bin/env python3

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backup_logger import get_logger

def test_logger():
    """Test the backup logger functionality."""
    
    print("=" * 60)
    print("TESTING BACKUP LOGGER MODULE")
    print("=" * 60)
    
    logger = get_logger(
        name="test_backup",
        log_dir="./test_logs",
        log_level="DEBUG",
        console_output=True
    )
    
    print("\n1. Testing system events...")
    logger.log_system_event("Backup system initialized", "INFO")
    logger.log_system_event("Starting file monitoring...", "INFO")
    
    print("\n2. Testing file detection...")
    logger.log_file_detected("/source/document.pdf", "created")
    logger.log_file_detected("/source/image.jpg", "modified")
    
    print("\n3. Testing successful backup...")
    test_file = "/source/test_document.pdf"
    file_size = 1024 * 1024  # 1 MB
    
    logger.log_backup_start(test_file, file_size)
    time.sleep(0.5)
    
    logger.log_backup_success(
        file_path=test_file,
        destination="/backup/test_document.pdf",
        file_size=file_size,
        duration=0.5
    )
    
    print("\n4. Testing another successful backup...")
    logger.log_backup_success(
        file_path="/source/large_file.zip",
        destination="/backup/large_file.zip",
        file_size=50 * 1024 * 1024,
        duration=2.3
    )
    
    print("\n5. Testing failed backup...")
    logger.log_backup_failure(
        file_path="/source/corrupted.txt",
        error="Connection timeout",
        file_size=2048
    )
    
    logger.log_backup_failure(
        file_path="/source/locked.docx",
        error="Permission denied: File is locked by another process"
    )
    
    print("\n6. Testing more backups...")
    for i in range(3):
        logger.log_backup_success(
            file_path=f"/source/batch_file_{i}.txt",
            destination=f"/backup/batch_file_{i}.txt",
            file_size=512 * (i + 1),
            duration=0.1 * (i + 1)
        )
    
    print("\n7. Displaying statistics...")
    logger.print_stats()
    
    print("\n8. Getting stats as dictionary...")
    stats = logger.get_stats()
    print(f"Stats object: {stats}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    print(f"\nCheck logs in: ./test_logs/")
    print("- backup_YYYYMMDD.log (text log)")
    print("- backup_YYYYMMDD.json (structured JSON log)")
    
    return logger

if __name__ == "__main__":
    logger = test_logger()
