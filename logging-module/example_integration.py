#!/usr/bin/env python3
"""
Example: How to integrate logging module into Watcher Service
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from backup_logger import get_logger

class WatcherService:
    """Example Watcher Service with integrated logging."""
    
    def __init__(self, source_dir, backup_dir, log_dir="./logs"):
        """Initialize watcher with logger."""
        self.source_dir = Path(source_dir)
        self.backup_dir = Path(backup_dir)
        
        self.logger = get_logger(
            name="watcher_service",
            log_dir=log_dir,
            log_level="INFO"
        )
        
        self.logger.log_system_event("Watcher Service initialized")
        self.logger.log_system_event(f"Monitoring: {self.source_dir}")
        self.logger.log_system_event(f"Backup to: {self.backup_dir}")
    
    def on_file_created(self, file_path):
        """Handle file creation event."""
        self.logger.log_file_detected(str(file_path), "created")
        self.backup_file(file_path)
    
    def on_file_modified(self, file_path):
        """Handle file modification event."""
        self.logger.log_file_detected(str(file_path), "modified")
        self.backup_file(file_path)
    
    def backup_file(self, file_path):
        """
        Backup a file and log the operation.
        This is where you integrate with Storage Service.
        """
        try:
            file_size = file_path.stat().st_size
            
            self.logger.log_backup_start(str(file_path), file_size)
            
            start_time = time.time()
            
            time.sleep(0.5)
            
            destination = self.backup_dir / file_path.name

            duration = time.time() - start_time
            
            self.logger.log_backup_success(
                file_path=str(file_path),
                destination=str(destination),
                file_size=file_size,
                duration=duration
            )
            
        except Exception as e:
            self.logger.log_backup_failure(
                file_path=str(file_path),
                error=str(e),
                file_size=file_size if 'file_size' in locals() else None
            )
    
    def start(self):
        """Start watching (simplified example)."""
        self.logger.log_system_event("Watcher started", "INFO")
    
        
    def stop(self):
        """Stop watching and show stats."""
        self.logger.log_system_event("Watcher stopping...", "INFO")
        self.logger.print_stats()


# Example usage in watcher-service/watcher.py

def main():
    """Main function for watcher service."""
    
    watcher = WatcherService(
        source_dir="/app/source",
        backup_dir="/app/backup",
        log_dir="/app/logs"
    )
    
    try:
        watcher.start()
        
        print("Watcher running... Press Ctrl+C to stop")
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        watcher.stop()


if __name__ == "__main__":
    main()


# How to use in actual Watcher Service:

"""
# In watcher-service/watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
sys.path.insert(0, '../logging-module')
from backup_logger import get_logger

class BackupEventHandler(FileSystemEventHandler):
    def __init__(self, storage_client):
        self.storage_client = storage_client
        self.logger = get_logger(name="watcher", log_dir="/app/logs")
        
    def on_created(self, event):
        if not event.is_directory:
            self.logger.log_file_detected(event.src_path, "created")
            self.backup_file(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self.logger.log_file_detected(event.src_path, "modified")
            self.backup_file(event.src_path)
    
    def backup_file(self, file_path):
        import time
        from pathlib import Path
        
        try:
            file_size = Path(file_path).stat().st_size
            self.logger.log_backup_start(file_path, file_size)
            
            start = time.time()
            
            # Upload to storage
            response = self.storage_client.upload(file_path)
            
            duration = time.time() - start
            
            self.logger.log_backup_success(
                file_path=file_path,
                destination=response['destination'],
                file_size=file_size,
                duration=duration
            )
        except Exception as e:
            self.logger.log_backup_failure(file_path, str(e))
"""
