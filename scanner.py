# ============================================================
# 模块：统一扫描器 (scanner.py)
# ============================================================
import os
import time
from datetime import datetime
import config
import utils

class UnifiedScanner:
    def __init__(self, paths, log_callback, progress_callback, complete_callback,
                 project_size_cache=None, project_hash_cache=None,
                 file_size_cache=None, file_hash_cache=None):
        self.paths = paths
        self.log = log_callback
        self.progress = progress_callback
        self.complete = complete_callback
        self.project_size_cache = project_size_cache or {}
        self.project_hash_cache = project_hash_cache or {}
        self.file_size_cache = file_size_cache or {}
        self.file_hash_cache = file_hash_cache or {}
        self.stop_flag = False
        self.result = {
            "scan_time": datetime.now().isoformat(),
            "root_paths": paths,
            "projects": [],
            "all_files": []
        }

    def stop(self):
        self.stop_flag = True

    def _scan_folder_with_cache(self, folder, size_cache, hash_cache):
        current_size = utils.get_folder_total_size(folder)
        cached_size = size_cache.get(folder)
        if cached_size is not None and current_size == cached_size and folder in hash_cache:
            self.log(f"[复用] {folder} 大小未变")
            return hash_cache[folder], True, current_size
        self.log(f"扫描: {folder} ({utils.format_size(current_size)})")
        hashes = {}
        file_count = 0
        for root, dirs, files in os.walk(folder):
            if self.stop_flag:
                break
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, folder)
                h = utils.compute_file_hash(full_path)
                if h:
                    hashes[rel_path] = h
                file_count += 1
                if file_count % 100 == 0:
                    self.progress(f"已处理 {file_count} 个文件...")
                    time.sleep(0.01)
            for d in dirs:
                sub_folder = os.path.join(root, d)
                size_cache[sub_folder] = utils.get_folder_total_size(sub_folder)
        size_cache[folder] = current_size
        hash_cache[folder] = hashes
        return hashes, False, current_size

    def scan(self):
        for scan_root in self.paths:
            if self.stop_flag:
                break
            if not os.path.exists(scan_root):
                self.log(f"[警告] 路径不存在: {scan_root}")
                continue
            try:
                for entry in os.listdir(scan_root):
                    full = os.path.join(scan_root, entry)
                    if os.path.isdir(full):
                        hashes, reused, _ = self._scan_folder_with_cache(
                            full, self.project_size_cache, self.project_hash_cache)
                        self.result["projects"].append({
                            "path": full,
                            "name": entry,
                            "hashes": hashes,
                            "reused": reused
                        })
            except Exception as e:
                self.log(f"读取目录失败 {scan_root}: {e}")

            all_hashes, _, _ = self._scan_folder_with_cache(
                scan_root, self.file_size_cache, self.file_hash_cache)
            for rel_path, h in all_hashes.items():
                full_path = os.path.join(scan_root, rel_path)
                try:
                    stat = os.stat(full_path)
                    self.result["all_files"].append({
                        "path": full_path,
                        "size": stat.st_size,
                        "mtime": stat.st_mtime,
                        "hash": h
                    })
                except:
                    pass
        self.complete(self.result, self.stop_flag)
