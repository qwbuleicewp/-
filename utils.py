# ============================================================
# 模块：通用工具函数 (utils.py)  优化 truncate_text
# ============================================================
import os
import io
import base64
import hashlib
import subprocess
import platform
from PIL import Image, ImageTk
import send2trash
import config

def get_folder_total_size(folder_path):
    total = 0
    try:
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
    except:
        pass
    return total

def compute_file_hash(path, block_size=65536):
    md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(block_size), b""):
                md5.update(chunk)
        return md5.hexdigest()
    except:
        return None

def get_next_id(projects_lists):
    max_id = 0
    for lst in projects_lists:
        for p in lst:
            try:
                pid = int(p.get("id", 0))
                max_id = max(max_id, pid)
            except:
                continue
    return max_id + 1

def compress_image_to_base64(image_path, target_size=None, quality=75):
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        if target_size:
            target_w, target_h = target_size
            img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            new_img = Image.new('RGB', (target_w, target_h), (255, 255, 255))
            paste_x = (target_w - img.width) // 2
            paste_y = (target_h - img.height) // 2
            new_img.paste(img, (paste_x, paste_y))
            img = new_img
        else:
            new_size = (int(img.width * 0.2), int(img.height * 0.2))
            img.thumbnail(new_size, Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        img_data = buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        print(f"图片压缩失败: {e}")
        return None

def base64_to_thumbnail(base64_str, size=config.THUMBNAIL_SIZE):
    if not base64_str:
        return None
    try:
        img_data = base64.b64decode(base64_str)
        img = Image.open(io.BytesIO(img_data))
        if img.size != size:
            img.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"缩略图生成失败: {e}")
        return None

def open_file_or_folder(path):
    if not os.path.exists(path):
        return
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', path])
    else:
        subprocess.run(['xdg-open', path])

def safe_delete(paths):
    for p in paths:
        try:
            if os.path.exists(p):
                send2trash.send2trash(p)
        except Exception as e:
            print(f"删除失败 {p}: {e}")

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def get_video_info(path):
    try:
        import moviepy.editor as mp
        clip = mp.VideoFileClip(path)
        duration = clip.duration
        size = os.path.getsize(path)
        info = f"时长: {int(duration//60)}:{int(duration%60):02d}\n大小: {format_size(size)}\n分辨率: {clip.w}x{clip.h}"
        clip.close()
        return info
    except ImportError:
        return "未安装 moviepy"
    except Exception as e:
        return f"无法读取视频信息: {e}"

def truncate_text(text, max_width, font):
    """截断文本使其不超过给定宽度，超出部分用省略号替代"""
    if not text:
        return ""
    import tkinter.font as tkfont
    f = tkfont.Font(family=font[0], size=font[1], weight=font[2] if len(font) > 2 else 'normal')
    # 如果文本宽度小于等于最大宽度，直接返回
    if f.measure(text) <= max_width:
        return text
    # 否则逐字缩短并添加省略号
    while len(text) > 0:
        text = text[:-1]
        if f.measure(text + "…") <= max_width:
            return text + "…"
    return "…"

def truncate_text(text, max_width, font):
    """简单截断，永远返回至少一个字符（空格或原文字）"""
    if not text:
        return " "
    # 粗略按字体大小估算最大字符数
    avg_char_width = font[1]  # 字号
    max_chars = max(1, int(max_width / avg_char_width) - 2)
    if len(text) > max_chars:
        return text[:max_chars] + "…"
    return text

