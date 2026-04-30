# ============================================================
# 模块：全局配置 (config.py)
# ============================================================
import os
import hashlib

CONFIG_FILE = "warehouse_tool_config.json"
PROJECTS_FILE = "projects.json"
SCAN_DATA_FILE = "scan_data.json"
DEFAULT_LOCATION = "待定"
THUMBNAIL_SIZE = (150, 150)
EDIT_PREVIEW_SIZE = (200, 200)

ROW_HEIGHT = 180
FILTER_ROW_HEIGHT = 44
HEADER_ROW_HEIGHT = 44
BUFFER_ROWS = 3

COLUMNS = [
    {"key": "pic",    "name": "图片", "width": 160, "stretch": False},
    {"key": "num",    "name": "编号", "width": 60,  "stretch": False},
    {"key": "name",   "name": "名字", "width": 200, "stretch": True},
    {"key": "tags",   "name": "标签", "width": 200, "stretch": True},
    {"key": "desc",   "name": "介绍", "width": 250, "stretch": True},
    {"key": "loc",    "name": "位置", "width": 100, "stretch": True},
    {"key": "action", "name": "操作", "width": 120, "stretch": False},
]

POWER_MODE_NORMAL = "normal"
POWER_MODE_LOW = "low"

DUP_BY_HASH        = 1
DUP_BY_SIZE        = 2
DUP_BY_NAME_SIM    = 4
DUP_BY_IMAGE_SIM   = 8
DUP_BY_MTIME       = 16
DUP_BY_VIDEO_SIM   = 32
DUP_BY_ARCHIVE_SIM = 64

DUPLICATE_CACHE_FILE = "duplicate_cache.json"
HASH_ALGO = hashlib.md5

BASE_FONT   = ('Microsoft YaHei', 15)
BOLD_FONT   = ('Microsoft YaHei', 15, 'bold')
BUTTON_FONT = ('Microsoft YaHei', 15, 'bold')

# 新增：主视图模式
VIEW_MODE_TABLE = "table"
VIEW_MODE_THUMBNAIL = "thumbnail"
