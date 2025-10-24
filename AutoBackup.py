import os
import time
import zipfile
import shutil
import argparse
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class BackupHandler(FileSystemEventHandler):
    def __init__(self, source_path, backup_dir, buffer_size, cooldown, use_zip, log):
        self.source_path = source_path
        self.backup_dir = backup_dir
        self.buffer_size = buffer_size
        self.cooldown = cooldown
        self.use_zip = use_zip
        self.log = log

        self.last_change_time = 0
        self.last_backup_time = 0

    def on_any_event(self, event):
        if not event.is_directory:
            self.last_change_time = time.time()

    def should_backup(self):
        return ( self.last_change_time > self.last_backup_time and (time.time() - self.last_change_time) >= self.cooldown)

    def create_backup(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"{os.path.basename(self.source_path)}_{timestamp}"

        if self.use_zip:
            zip_path = os.path.join(self.backup_dir, backup_name + ".zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(self.source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zip_name = os.path.relpath(file_path, self.source_path)
                        zipf.write(file_path, zip_name)
            self.log_message(f"[BACKUP] Created ZIP: {zip_path}")
        else:
            dest_folder = os.path.join(self.backup_dir, backup_name)
            shutil.copytree(self.source_path, dest_folder)
            self.log_message(f"[BACKUP] Copied folder: {dest_folder}")

        self.last_backup_time = time.time()
        self.cleanup_backups()

    def cleanup_backups(self):
        if self.buffer_size <= 0:
            return
        items = sorted(
            [f for f in os.listdir(self.backup_dir) if f.endswith(".zip") or os.path.isdir(os.path.join(self.backup_dir, f))],
            key=lambda x: os.path.getmtime(os.path.join(self.backup_dir, x)),
            reverse=True,
        )
        for old in items[self.buffer_size:]:
            path = os.path.join(self.backup_dir, old)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            self.log_message(f"[CLEANUP] Removed old backup: {old}")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        full_msg = f"[{timestamp}] {message}"
        print(full_msg)
        self.log.write(full_msg + "\n")
        self.log.flush()


def start(source_path, backup_path, buffer_size, cooldown, use_zip):
    if not os.path.exists(source_path):
        print(f"[ERROR] Source path does not exist: {source_path}")
        return

    backup_dir = backup_path or os.path.join(os.path.dirname(source_path), "AutoBackups")
    os.makedirs(backup_dir, exist_ok=True)

    log_file_path = os.path.join(backup_dir, "backup_log.txt")
    log = open(log_file_path, "a", encoding="utf-8")

    handler = BackupHandler(source_path, backup_dir, buffer_size, cooldown, use_zip, log)
    observer = Observer()
    observer.schedule(handler, source_path, recursive=True)
    observer.start()

    handler.log_message(f"[INFO] Watching source: {source_path}")
    handler.log_message(f"[INFO] Backups stored in: {backup_dir}")
    handler.log_message(f"[INFO] Cooldown={cooldown}s, Buffer={buffer_size}, ZIP={use_zip}")
    handler.log_message("-" * 60)

    try:
        while True:
            time.sleep(1)
            if handler.should_backup():
                handler.create_backup()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatic backup system using watchdog.")
    parser.add_argument("--source-path", required=True, help="Path to the directory")
    parser.add_argument("--backup-path", help="Optional backup folder (default: AutoBackups next to the source file)")
    parser.add_argument("--buffer-size", type=int, default=5, help="Number of backups to keep (numbers <= 0 means infinite)")
    parser.add_argument("--cooldown", type=int, default=5, help="Cooldown after last file change before backup in seconds (to prevent multiple backups on multiple changes)")
    parser.add_argument("--zip", action="store_true", help="Enable ZIP backup")
    args = parser.parse_args()

    start(args.source_path, args.backup_path, args.buffer_size, args.cooldown, args.zip)
