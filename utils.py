import sys
import os
import ctypes
import psutil
import shutil

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_locking_processes(folder_path):
    locking_procs = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for item in proc.open_files():
                if folder_path.lower() in item.path.lower():
                    if proc not in locking_procs:
                        locking_procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return locking_procs

def get_free_space(folder_path):
    try:
        # Mengambil huruf drive (misal C: atau D:) dari path
        drive = os.path.splitdrive(os.path.abspath(folder_path))[0]
        if not drive:
            drive = os.path.abspath(folder_path)
        return shutil.disk_usage(drive).free
    except Exception:
        return 0

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"