import time
import os
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

STORAGE_ENDPOINT = os.getenv("STORAGE_ENDPOINT", "http://storage:8000/upload")
WATCH_DIR = os.getenv("WATCH_DIR", "/app/source")

class FileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            self.upload(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.upload(event.src_path)

    def upload(self, path):
        try:
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f)}
                r = requests.post(STORAGE_ENDPOINT, files=files, timeout=10)
                print(f"[UPLOAD] {path} -> {r.status_code}")
        except Exception as e:
            print(f"[ERROR] {path}: {e}")

if __name__ == "__main__":
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
