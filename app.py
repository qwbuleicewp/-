# ============================================================
# 模块：主应用类 (app.py)
# 整合所有 Mixin，构成完整的 WarehouseApp
# ============================================================

import os
import json
import threading
import sys
import tkinter as tk
from tkinter import messagebox
import config
import utils
from power_manager import PowerManager
from scanner import UnifiedScanner
from duplicate_engine import DuplicateEngine
from video_player import VideoPlayer

from warehouse_ui import WarehouseUIMixin
from warehouse_actions import WarehouseActionsMixin
from scan_dialog import ScanDialogMixin
from edit_dialog import EditDialogMixin
from alias_dialog import AliasDialogMixin
from tray import TrayMixin
from duplicate_ui import DuplicateUIMixin
from duplicate_preview import DuplicatePreviewMixin
from duplicate_actions import DuplicateActionsMixin

class WarehouseApp(
    WarehouseUIMixin,
    WarehouseActionsMixin,
    ScanDialogMixin,
    EditDialogMixin,
    AliasDialogMixin,
    TrayMixin,
    DuplicateUIMixin,
    DuplicatePreviewMixin,
    DuplicateActionsMixin
):
    def __init__(self, root):
        self.root = root
        self.root.title("仓库管理工具")
        self.root.geometry("1630x900")
        self.root.state('zoomed')
        self.root.resizable(True, True)
        self.root.configure(bg="#f5f7fa")
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
            self.root.tk.call('tk', 'scaling', 1.25)
        except:
            pass

        self.base_font = config.BASE_FONT
        self.bold_font = config.BOLD_FONT
        self.button_font = config.BUTTON_FONT
        self.root.option_add('*Font', self.base_font)
        self.root.option_add('*Foreground', '#000000')

        # 数据容器
        self.projects = []
        self.secondary_projects = []
        self.cache_projects = []
        self.cache_secondary = []
        self.alias_map = {}
        self.all_tags_primary = set()
        self.all_tags_secondary = set()
        self.preset_tags = set()

        self.current_view = "warehouse"
        self.warehouse_view_mode = config.VIEW_MODE_TABLE
        self.sort_column = "num"
        self.sort_asc = True
        self.filter_name = ""
        self.filter_tags = ""
        self.filter_desc = ""
        self.filter_location = ""

        # 扫描路径（主 / 副独立）
        self.main_scan_paths = []
        self.secondary_scan_paths = []
        self.scan_target_cache = "main"      # 保留，可能用于兼容
        self.scan_dialog = None
        self.project_size_cache = {}
        self.project_hash_cache = {}
        self.file_size_cache = {}
        self.file_hash_cache = {}
        self.scan_auto_close_id = None

        self.edit_win = None
        self.current_edit_id = None

        self.thumbnail_cache = {}
        self.filtered_list = []
        self.total_items = 0
        self.data_canvas = None
        self.row_images = {}
        self.col_widths = [c["width"] for c in config.COLUMNS]
        self.resize_after_id = None
        self.redraw_after_id = None
        self.filter_menu_cache = {"name": [], "tags": [], "desc": [], "loc": []}
        self.filter_menu_dirty = True

        self.default_save_path = os.path.join(os.getcwd(), config.PROJECTS_FILE)

        self.power_mode = config.POWER_MODE_NORMAL
        self.power_manager = PowerManager(self.power_mode)

        self.tray_icon = None
        self.tray_thread = None
        self.scan_progress_win = None
        self.unified_scanner = None
        self.scan_thread = None
        self.scan_button = None
        self.scan_log_text = None
        self.scan_progress_bar = None

        # 查重相关
        self.duplicate_frame = None
        self.dup_scan_data = None
        self.dup_groups = []
        self.dup_selected_nodes = set()
        self.dup_keep_index = {}
        self.dup_tree = None
        self.dup_check_vars = {}
        self.selected_preview_paths = [None, None]
        self.current_group_files = []
        self.preview_titles = [None, None]
        self.preview_labels = [None, None]
        self.preview_infos = [None, None]
        self.video_players = [None, None]
        self._archive_cache = {}
        self.archive_internal_state = [None, None]
        self.dup_progress_win = None
        self.dup_engine = None
        self.dup_stop_flag = False
        self.dup_insert_batch_id = None
        self._syncing_scroll = False

        # 初始化流程
        self.load_config()
        self.load_projects()
        self.load_scan_cache()
        self.init_ui()
        self.build_duplicate_ui()
        self.update_data_and_redraw()
        self.highlight_view_button()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.setup_tray()
        self.root.bind("<Control-s>", lambda e: self.save_all())
        self.root.bind("<Control-S>", lambda e: self.save_all())

    # ---------- 配置管理 ----------
    def load_config(self):
        if os.path.exists(config.CONFIG_FILE):
            try:
                with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                self.main_scan_paths = cfg.get("main_scan_paths", [])
                self.secondary_scan_paths = cfg.get("secondary_scan_paths", [])
                self.power_mode = cfg.get("power_mode", config.POWER_MODE_NORMAL)
            except:
                self.main_scan_paths = []
                self.secondary_scan_paths = []
        else:
            self.main_scan_paths = []
            self.secondary_scan_paths = []

    def save_config(self):
        cfg = {
            "main_scan_paths": self.main_scan_paths,
            "secondary_scan_paths": self.secondary_scan_paths,
            "power_mode": self.power_mode
        }
        try:
            with open(config.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except:
            pass

    def load_projects(self):
        if os.path.exists(self.default_save_path):
            try:
                with open(self.default_save_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.projects = data.get("projects", [])
                self.secondary_projects = data.get("secondaryProjects", [])
                self.cache_projects = data.get("cacheProjects", [])
                self.cache_secondary = data.get("cacheProjectsSecondary", [])
                self.alias_map = {k.lower(): v for k, v in dict(data.get("aliasMap", [])).items()}
                self.all_tags_primary = set(data.get("allTagsPrimary", []))
                self.all_tags_secondary = set(data.get("allTagsSecondary", []))
                self.preset_tags = set(data.get("presetTags", []))
            except Exception as e:
                print(f"加载项目失败: {e}")

    def save_projects(self):
        data = {
            "projects": self.projects,
            "secondaryProjects": self.secondary_projects,
            "cacheProjects": self.cache_projects,
            "cacheProjectsSecondary": self.cache_secondary,
            "aliasMap": list(self.alias_map.items()),
            "allTagsPrimary": list(self.all_tags_primary),
            "allTagsSecondary": list(self.all_tags_secondary),
            "presetTags": list(self.preset_tags)
        }
        try:
            with open(self.default_save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def load_scan_cache(self):
        if os.path.exists(config.SCAN_DATA_FILE):
            try:
                with open(config.SCAN_DATA_FILE, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                self.project_size_cache = cache.get("project_size_cache", {})
                self.project_hash_cache = cache.get("project_hash_cache", {})
                self.file_size_cache = cache.get("file_size_cache", {})
                self.file_hash_cache = cache.get("file_hash_cache", {})
                self.dup_scan_data = cache.get("last_scan_result")
            except:
                pass

    def save_scan_cache(self):
        cache = {
            "project_size_cache": self.project_size_cache,
            "project_hash_cache": self.project_hash_cache,
            "file_size_cache": self.file_size_cache,
            "file_hash_cache": self.file_hash_cache,
            "last_scan_result": self.dup_scan_data
        }
        try:
            with open(config.SCAN_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except:
            pass

    def save_all(self):
        self.save_projects()
        self.save_scan_cache()
        self.save_duplicate_cache()
        self.save_config()
        messagebox.showinfo("成功", "所有数据已保存")

    def _find_project_by_id(self, pid):
        for lst in [self.projects, self.secondary_projects, self.cache_projects, self.cache_secondary]:
            for p in lst:
                if p["id"] == pid:
                    return p
        return None

    def highlight_view_button(self):
        for v, btn in self.view_btns.items():
            btn.configure(style="ActiveView.TButton" if v == self.current_view else "Large.TButton")

    def switch_view(self, view):
        if view == self.current_view:
            return
        self.current_view = view
        self.data_canvas.pack_forget()
        self.duplicate_frame.pack_forget()
        if view == "duplicate":
            self.header_canvas.pack_forget()
            self.filter_canvas.pack_forget()
            self.duplicate_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            if self.dup_scan_data:
                self.root.after(50, self._update_dup_ui_after_scan)
        else:
            self.header_canvas.pack(fill=tk.X, pady=0, before=self.data_container)
            self.filter_canvas.pack(fill=tk.X, pady=0, before=self.data_container)
            self.data_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.update_data_and_redraw()
        self.highlight_view_button()

if __name__ == "__main__":
    root = tk.Tk()
    app = WarehouseApp(root)
    root.mainloop()
