# ============================================================
# 模块：查重引擎 (duplicate_engine.py)
# ============================================================
import os
import hashlib
from collections import defaultdict
from PIL import Image
import imagehash
import config

try:
    import videohash
    VIDEOHASH_AVAILABLE = True
except ImportError:
    VIDEOHASH_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

class DuplicateEngine:
    def __init__(self, files, options):
        self.files = files
        self.options = options
        self.hash_cache = {}
        self.image_hash_cache = {}
        self.video_hash_cache = {}
        self.archive_manifest_cache = {}
        self.stop_flag = False

    def stop(self):
        self.stop_flag = True

    def compute_file_hash(self, path, file_info=None):
        if file_info and 'hash' in file_info:
            return file_info['hash']
        if path in self.hash_cache:
            return self.hash_cache[path]
        h = __import__('utils').compute_file_hash(path)
        if h:
            self.hash_cache[path] = h
        return h

    def compute_image_hash(self, path):
        if path in self.image_hash_cache:
            return self.image_hash_cache[path]
        try:
            img = Image.open(path)
            h = imagehash.phash(img)
            self.image_hash_cache[path] = h
            return h
        except:
            return None

    def is_image_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')

    def is_video_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v')

    def is_archive_file(self, path):
        ext = os.path.splitext(path)[1].lower()
        return ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2')

    def compute_video_hash(self, path, method='fast'):
        if path in self.video_hash_cache:
            return self.video_hash_cache[path]
        h = None
        if method == 'fast' and VIDEOHASH_AVAILABLE:
            try:
                h = videohash.VideoHash(path).hash
            except:
                pass
        elif method == 'accurate' and OPENCV_AVAILABLE:
            try:
                cap = cv2.VideoCapture(path)
                frames = []
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                if total > 0:
                    for i in range(10):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, i * total // 10)
                        ret, frame = cap.read()
                        if ret:
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(frame_rgb)
                            frames.append(imagehash.phash(pil_img))
                cap.release()
                if frames:
                    h = sum(frames, start=imagehash.ImageHash)
            except:
                pass
        if h is not None:
            self.video_hash_cache[path] = h
        return h

    def compute_archive_manifest(self, path):
        if path in self.archive_manifest_cache:
            return self.archive_manifest_cache[path]
        manifest = []
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == '.zip':
                import zipfile
                with zipfile.ZipFile(path, 'r') as zf:
                    for name in zf.namelist():
                        info = zf.getinfo(name)
                        manifest.append((name, info.file_size))
            elif ext in ('.tar', '.gz', '.bz2'):
                import tarfile
                mode = 'r:gz' if ext == '.gz' else 'r:bz2' if ext == '.bz2' else 'r'
                with tarfile.open(path, mode) as tf:
                    for member in tf.getmembers():
                        if member.isfile():
                            manifest.append((member.name, member.size))
            elif ext == '.rar':
                try:
                    import rarfile
                    with rarfile.RarFile(path, 'r') as rf:
                        for name in rf.namelist():
                            info = rf.getinfo(name)
                            manifest.append((name, info.file_size))
                except ImportError:
                    pass
            elif ext == '.7z':
                try:
                    import py7zr
                    with py7zr.SevenZipFile(path, 'r') as szf:
                        for name, info in szf.getnames():
                            manifest.append((name, info.size))
                except ImportError:
                    pass
        except:
            pass
        manifest.sort(key=lambda x: x[0])
        self.archive_manifest_cache[path] = manifest
        return manifest

    def find_duplicates(self, progress_callback=None):
        n = len(self.files)
        parent = list(range(n))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        mode = self.options.get('mode_flags', config.DUP_BY_HASH)
        video_method = self.options.get('video_method', 'fast')
        size_groups = defaultdict(list)
        for i, f in enumerate(self.files):
            size_groups[f['size']].append(i)

        if self.stop_flag:
            return []

        processed = 0
        total_ops = 1
        if mode & config.DUP_BY_HASH:
            total_ops += len([g for g in size_groups.values() if len(g) >= 2])
        if mode & config.DUP_BY_IMAGE_SIM:
            total_ops += sum(1 for f in self.files if self.is_image_file(f['path']))
        if mode & config.DUP_BY_VIDEO_SIM:
            total_ops += sum(1 for f in self.files if self.is_video_file(f['path']))
        if mode & config.DUP_BY_ARCHIVE_SIM:
            total_ops += sum(1 for f in self.files if self.is_archive_file(f['path']))

        if mode & config.DUP_BY_HASH:
            hash_groups = defaultdict(list)
            for indices in size_groups.values():
                if self.stop_flag:
                    return []
                if len(indices) < 2:
                    continue
                for i in indices:
                    f = self.files[i]
                    h = self.compute_file_hash(f['path'], f)
                    if h:
                        hash_groups[h].append(i)
                processed += 1
                if progress_callback and processed % 10 == 0:
                    progress_callback(processed, total_ops, "计算文件哈希...")
            for indices in hash_groups.values():
                if len(indices) >= 2:
                    first = indices[0]
                    for other in indices[1:]:
                        union(first, other)

        if self.stop_flag:
            return []

        if mode & config.DUP_BY_SIZE and not (mode & config.DUP_BY_HASH):
            for indices in size_groups.values():
                if len(indices) >= 2:
                    first = indices[0]
                    for other in indices[1:]:
                        union(first, other)

        if mode & config.DUP_BY_NAME_SIM:
            threshold = self.options.get('name_threshold', 0.8)
            name_len_groups = defaultdict(list)
            for i, f in enumerate(self.files):
                name = os.path.basename(f['path'])
                name_len_groups[len(name)].append(i)
            for indices in name_len_groups.values():
                if self.stop_flag:
                    return []
                if len(indices) < 2:
                    continue
                for a in range(len(indices)):
                    i = indices[a]
                    name_i = os.path.basename(self.files[i]['path'])
                    for b in range(a+1, len(indices)):
                        j = indices[b]
                        name_j = os.path.basename(self.files[j]['path'])
                        if self._similar_text(name_i, name_j) >= threshold:
                            union(i, j)

        if self.stop_flag:
            return []

        if mode & config.DUP_BY_IMAGE_SIM:
            threshold = self.options.get('image_threshold', 10)
            img_indices = [i for i, f in enumerate(self.files) if self.is_image_file(f['path'])]
            size_tolerance = 0.1
            img_processed = 0
            for i in range(len(img_indices)):
                if self.stop_flag:
                    return []
                idx_i = img_indices[i]
                f_i = self.files[idx_i]
                h_i = self.compute_image_hash(f_i['path'])
                img_processed += 1
                if progress_callback and img_processed % 10 == 0:
                    progress_callback(processed + img_processed, total_ops, "计算图片哈希...")
                if h_i is None:
                    continue
                for j in range(i+1, len(img_indices)):
                    idx_j = img_indices[j]
                    f_j = self.files[idx_j]
                    if f_i['size'] > 0 and f_j['size'] > 0:
                        ratio = abs(f_i['size'] - f_j['size']) / max(f_i['size'], f_j['size'])
                        if ratio > size_tolerance:
                            continue
                    h_j = self.compute_image_hash(f_j['path'])
                    if h_j is None:
                        continue
                    if h_i - h_j <= threshold:
                        union(idx_i, idx_j)

        if self.stop_flag:
            return []

        if mode & config.DUP_BY_VIDEO_SIM:
            threshold = self.options.get('video_threshold', 15)
            video_indices = [i for i, f in enumerate(self.files) if self.is_video_file(f['path'])]
            video_processed = 0
            for i in range(len(video_indices)):
                if self.stop_flag:
                    return []
                idx_i = video_indices[i]
                f_i = self.files[idx_i]
                h_i = self.compute_video_hash(f_i['path'], video_method)
                video_processed += 1
                if progress_callback and video_processed % 5 == 0:
                    progress_callback(processed + img_processed + video_processed, total_ops, "计算视频哈希...")
                if h_i is None:
                    continue
                for j in range(i+1, len(video_indices)):
                    idx_j = video_indices[j]
                    f_j = self.files[idx_j]
                    h_j = self.compute_video_hash(f_j['path'], video_method)
                    if h_j is None:
                        continue
                    if isinstance(h_i, imagehash.ImageHash) and isinstance(h_j, imagehash.ImageHash):
                        if h_i - h_j <= threshold:
                            union(idx_i, idx_j)
                    elif isinstance(h_i, str) and isinstance(h_j, str):
                        if self._hamming_distance(h_i, h_j) <= threshold:
                            union(idx_i, idx_j)

        if self.stop_flag:
            return []

        if mode & config.DUP_BY_ARCHIVE_SIM:
            threshold = self.options.get('archive_threshold', 0.9)
            archive_indices = [i for i, f in enumerate(self.files) if self.is_archive_file(f['path'])]
            archive_processed = 0
            for i in range(len(archive_indices)):
                if self.stop_flag:
                    return []
                idx_i = archive_indices[i]
                f_i = self.files[idx_i]
                m_i = self.compute_archive_manifest(f_i['path'])
                archive_processed += 1
                if progress_callback and archive_processed % 5 == 0:
                    progress_callback(processed + img_processed + video_processed + archive_processed, total_ops, "分析压缩包...")
                if not m_i:
                    continue
                for j in range(i+1, len(archive_indices)):
                    idx_j = archive_indices[j]
                    f_j = self.files[idx_j]
                    m_j = self.compute_archive_manifest(f_j['path'])
                    if not m_j:
                        continue
                    if self._jaccard_similarity(m_i, m_j) >= threshold:
                        union(idx_i, idx_j)

        if mode & config.DUP_BY_MTIME:
            diff = self.options.get('mtime_diff', 60)
            sorted_files = sorted(enumerate(self.files), key=lambda x: x[1]['mtime'])
            for i in range(len(sorted_files)):
                idx_i, f_i = sorted_files[i]
                for j in range(i+1, len(sorted_files)):
                    idx_j, f_j = sorted_files[j]
                    if abs(f_i['mtime'] - f_j['mtime']) <= diff:
                        union(idx_i, idx_j)
                    else:
                        break

        groups = defaultdict(list)
        for i in range(n):
            root = find(i)
            groups[root].append(self.files[i])
        return [g for g in groups.values() if len(g) >= 2]

    def _similar_text(self, s1, s2):
        if s1 == s2:
            return 1.0
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        if len1 > 50 or len2 > 50:
            if s1 in s2 or s2 in s1:
                return 0.9
            return 0.0
        prev = list(range(len2+1))
        for i in range(1, len1+1):
            curr = [i] + [0]*len2
            for j in range(1, len2+1):
                cost = 0 if s1[i-1]==s2[j-1] else 1
                curr[j] = min(prev[j]+1, curr[j-1]+1, prev[j-1]+cost)
            prev = curr
        dist = prev[len2]
        max_len = max(len1, len2)
        return 1.0 - dist/max_len

    def _hamming_distance(self, s1, s2):
        if len(s1) != len(s2):
            return float('inf')
        return sum(c1 != c2 for c1, c2 in zip(s1, s2))

    def _jaccard_similarity(self, m1, m2):
        set1 = set(m1)
        set2 = set(m2)
        inter = len(set1 & set2)
        union = len(set1 | set2)
        return inter / union if union else 0.0
