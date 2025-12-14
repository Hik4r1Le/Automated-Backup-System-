import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class BackupLogger:
    def __init__(
        self,
        name: str = "backup_system",
        log_dir: str = "./logs",
        log_level: str = "INFO",
        console_output: bool = True
    ):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        log_file = self.log_dir / f"backup_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        self.stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'total_size': 0
        }
    
    def log_backup_start(self, file_path: str, file_size: int):
        self.logger.info(
            f"Starting backup: {file_path} "
            f"(Size: {self._format_size(file_size)})"
        )
    
    def log_backup_success(
        self,
        file_path: str,
        destination: str,
        file_size: int,
        duration: float
    ):
        self.stats['total_backups'] += 1
        self.stats['successful_backups'] += 1
        self.stats['total_size'] += file_size
        
        self.logger.info(
            f"✓ Backup SUCCESS: {file_path} -> {destination} | "
            f"Size: {self._format_size(file_size)} | "
            f"Duration: {duration:.2f}s"
        )
        
        self._write_json_log({
            'timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'source': file_path,
            'destination': destination,
            'size_bytes': file_size,
            'size_formatted': self._format_size(file_size),
            'duration_seconds': round(duration, 2)
        })
    
    def log_backup_failure(
        self,
        file_path: str,
        error: str,
        file_size: Optional[int] = None
    ):
        self.stats['total_backups'] += 1
        self.stats['failed_backups'] += 1
        
        size_info = f"Size: {self._format_size(file_size)} | " if file_size else ""
        
        self.logger.error(
            f"✗ Backup FAILED: {file_path} | "
            f"{size_info}"
            f"Error: {error}"
        )
        
        self._write_json_log({
            'timestamp': datetime.now().isoformat(),
            'status': 'FAILED',
            'source': file_path,
            'size_bytes': file_size,
            'size_formatted': self._format_size(file_size) if file_size else None,
            'error': error
        })
    
    def log_file_detected(self, file_path: str, event_type: str):
        self.logger.info(f"File {event_type}: {file_path}")
    
    def log_system_event(self, message: str, level: str = "INFO"):
        log_func = getattr(self.logger, level.lower())
        log_func(message)
    
    def get_stats(self) -> Dict[str, Any]:
        if self.stats['total_backups'] > 0:
            success_rate = (
                self.stats['successful_backups'] / 
                self.stats['total_backups'] * 100
            )
        else:
            success_rate = 0
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 2),
            'total_size_formatted': self._format_size(self.stats['total_size'])
        }
    
    def print_stats(self):
        stats = self.get_stats()
        self.logger.info("=" * 50)
        self.logger.info("BACKUP STATISTICS")
        self.logger.info("=" * 50)
        self.logger.info(f"Total backups: {stats['total_backups']}")
        self.logger.info(f"Successful: {stats['successful_backups']}")
        self.logger.info(f"Failed: {stats['failed_backups']}")
        self.logger.info(f"Success rate: {stats['success_rate']}%")
        self.logger.info(f"Total size backed up: {stats['total_size_formatted']}")
        self.logger.info("=" * 50)
    
    def _format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _write_json_log(self, log_data: Dict[str, Any]):
        json_log_file = self.log_dir / f"backup_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            if json_log_file.exists():
                with open(json_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_data)
            
            with open(json_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self.logger.warning(f"Failed to write JSON log: {e}")


def get_logger(
    name: str = "backup_system",
    log_dir: str = "./logs",
    log_level: str = "INFO",
    console_output: bool = True
) -> BackupLogger:
    
    return BackupLogger(
        name=name,
        log_dir=log_dir,
        log_level=log_level,
        console_output=console_output
    )
