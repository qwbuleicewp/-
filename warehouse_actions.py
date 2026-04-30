# ============================================================
# 模块：仓库操作 (warehouse_actions.py)
# ============================================================
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import config
import utils

class WarehouseActionsMixin:
    def confirm_to_warehouse(self, pid):
    # 将缓存项目移到主仓库或副仓库
        cur = self.get_current_list()
        proj = next((p for p in cur if p["id"] == pid), None)
        if not proj:
            return
        if self.current_view == "cache":
            self.cache_projects = [p for p in self.cache_projects if p["id"] != pid]
            self.projects.append(proj)
        else:
            self.cache_secondary = [p for p in self.cache_secondary if p["id"] != pid]
            self.secondary_projects.append(proj)
        self.update_data_and_redraw()

    def delete_from_cache(self, pid):
        if messagebox.askyesno("确认删除", "确定从缓存中删除此项目吗？"):
            if self.current_view == "cache":
                self.cache_projects = [p for p in self.cache_projects if p["id"] != pid]
            else:
                self.cache_secondary = [p for p in self.cache_secondary if p["id"] != pid]
            self.update_data_and_redraw()

    def upload_image_for_project(self, pid):
        proj = self._find_project_by_id(pid)
        if not proj:
            return
        file_path = filedialog.askopenfilename(filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif")])
        if not file_path:
            return
        enc = utils.compress_image_to_base64(file_path, target_size=config.EDIT_PREVIEW_SIZE)
        if enc:
            proj["image"] = enc
            if pid in self.thumbnail_cache:
                del self.thumbnail_cache[pid]
            self.update_data_and_redraw()
            messagebox.showinfo("成功", "图片已上传")
        else:
            messagebox.showerror("错误", "图片压缩失败")

    def upload_and_copy_address(self, pid, addr):
        if addr:
            self.root.clipboard_clear()
            self.root.clipboard_append(addr.strip('"\''))
        self.upload_image_for_project(pid)

    def open_project_folder(self, path):
        if path and os.path.exists(path):
            utils.open_file_or_folder(path)
        else:
            messagebox.showwarning("警告", "路径不存在或为空")

    def load_data_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.projects = data.get("projects", [])
            self.secondary_projects = data.get("secondaryProjects", [])
            self.cache_projects = data.get("cacheProjects", [])
            self.cache_secondary = data.get("cacheProjectsSecondary", [])
            self.alias_map = {k.lower(): v for k, v in dict(data.get("aliasMap", [])).items()}
            self.all_tags_primary = set(data.get("allTagsPrimary", []))
            self.all_tags_secondary = set(data.get("allTagsSecondary", []))
            self.preset_tags = set(data.get("presetTags", []))
            self.update_data_and_redraw()
            messagebox.showinfo("成功", "数据已加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {e}")
