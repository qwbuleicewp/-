# ============================================================
# 模块：查重操作与树交互 (duplicate_actions.py) —— 修复滚动与复选框
# ============================================================
import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import defaultdict
import config
import utils
from duplicate_engine import DuplicateEngine

class DuplicateActionsMixin:
    def on_tree_click(self, event):
        item = self.dup_tree.identify_row(event.y)
        col = self.dup_tree.identify_column(event.x)
        if not item or col != '#0':
            return
        tags = self.dup_tree.item(item, "tags")
        if "file" in tags:
            self._toggle_file_check(item)
            path = self.dup_tree.set(item, "path")
            if path:
                self.selected_preview_paths = [path, self.selected_preview_paths[1]] if len(self.selected_preview_paths) > 1 else [path, None]
                self.current_group_files = []
                self._update_preview()
        elif "folder" in tags:
            self._toggle_folder_check(item)
        elif "group" in tags:
            self._toggle_group_check(item)

    def on_tree_right_click(self, event):
        item = self.dup_tree.identify_row(event.y)
        if not item:
            return
        if self.dup_tree.item(item, "open"):
            self.dup_tree.item(item, open=False)
        else:
            self.dup_tree.item(item, open=True)

    def _toggle_file_check(self, item):
        info = self.dup_check_vars.get(item)
        if info:
            info["var"].set(not info["var"].get())
            self._update_node_checkbox(item, info["var"].get())

    def _toggle_folder_check(self, item):
        state = not self._get_folder_check_state(item)
        for child in self.dup_tree.get_children(item):
            self._set_node_check(child, state)
        self._update_node_checkbox(item, state)

    def _toggle_group_check(self, item):
        state = not self._get_group_check_state(item)
        for child in self.dup_tree.get_children(item):
            self._set_node_check(child, state)
        self._update_node_checkbox(item, state)

    def _get_folder_check_state(self, item):
        for child in self.dup_tree.get_children(item):
            if self._get_node_check_state(child):
                return True
        return False

    def _get_group_check_state(self, item):
        for child in self.dup_tree.get_children(item):
            if self._get_node_check_state(child):
                return True
        return False

    def _get_node_check_state(self, item):
        tags = self.dup_tree.item(item, "tags")
        if "file" in tags:
            info = self.dup_check_vars.get(item)
            return info["var"].get() if info else False
        else:
            for child in self.dup_tree.get_children(item):
                if self._get_node_check_state(child):
                    return True
            return False

    def _set_node_check(self, item, state):
        tags = self.dup_tree.item(item, "tags")
        if "file" in tags:
            info = self.dup_check_vars.get(item)
            if info:
                info["var"].set(state)
                self._update_node_checkbox(item, state)
        else:
            for child in self.dup_tree.get_children(item):
                self._set_node_check(child, state)
            self._update_node_checkbox(item, state)

    def _update_node_checkbox(self, item, checked):
        text = self.dup_tree.item(item, "text")
        # 移除可能存在的旧复选框前缀
        for prefix in ("☑ ", "☐ ", "◼ "):
            if text.startswith(prefix):
                text = text[2:]
                break
        prefix = "☑ " if checked else "☐ "
        self.dup_tree.item(item, text=prefix + text)
        if checked:
            self._collect_checked_paths(item)
        else:
            self._remove_checked_paths(item)

    def _collect_checked_paths(self, item):
        tags = self.dup_tree.item(item, "tags")
        if "file" in tags:
            info = self.dup_check_vars.get(item)
            if info:
                self.dup_selected_nodes.add(info["path"])
        else:
            for child in self.dup_tree.get_children(item):
                self._collect_checked_paths(child)

    def _remove_checked_paths(self, item):
        tags = self.dup_tree.item(item, "tags")
        if "file" in tags:
            info = self.dup_check_vars.get(item)
            if info:
                self.dup_selected_nodes.discard(info["path"])
        else:
            for child in self.dup_tree.get_children(item):
                self._remove_checked_paths(child)

    def on_tree_double(self, event):
        item = self.dup_tree.identify_row(event.y)
        if not item:
            return
        tags = self.dup_tree.item(item, "tags")
        path = self.dup_tree.set(item, "path")
        if "file" in tags:
            group = self._find_group_by_path(path)
            if group:
                self.current_group_files = [f['path'] for f in group]
                first = self.current_group_files[0]
                self.selected_preview_paths = [first, path]
                self._update_preview()

    def _find_group_by_path(self, path):
        for g in self.dup_groups:
            if any(f['path'] == path for f in g):
                return g
        return None

    def _update_dup_ui_after_scan(self):
        if hasattr(self, 'dup_status') and self.dup_scan_data:
            count = len(self.dup_scan_data.get('files', []))
            self.dup_status.config(text=f"已加载 {count} 个文件")
        if hasattr(self, 'dup_tree'):
            self.dup_tree.delete(*self.dup_tree.get_children())
            self.dup_groups = []
            self.dup_selected_nodes.clear()
            self._update_preview()

    def create_dup_progress_window(self):
        if self.dup_progress_win and self.dup_progress_win.winfo_exists():
            self.dup_progress_win.destroy()
        win = tk.Toplevel(self.root)
        win.title("查重进度")
        win.geometry("400x150")
        win.configure(bg="#f5f7fa")
        win.protocol("WM_DELETE_WINDOW", self.on_dup_window_close)
        tk.Label(win, text="正在查重...", font=self.bold_font, bg="#f5f7fa").pack(pady=10)
        self.dup_progress_label = tk.Label(win, text="初始化...", font=self.base_font, bg="#f5f7fa")
        self.dup_progress_label.pack(pady=5)
        self.dup_progress_bar = ttk.Progressbar(win, mode='determinate', length=350)
        self.dup_progress_bar.pack(pady=10)
        btn_frame = tk.Frame(win, bg="#f5f7fa")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="停止查重", command=self.stop_duplicate_detection,
                  bg="#ffb6c1", font=self.button_font, padx=8).pack()
        self.dup_progress_win = win
        self.dup_stop_flag = False

    def on_dup_window_close(self):
        self.stop_duplicate_detection()
        if self.dup_progress_win:
            self.dup_progress_win.destroy()
            self.dup_progress_win = None

    def stop_duplicate_detection(self):
        self.dup_stop_flag = True
        if self.dup_engine:
            self.dup_engine.stop()

    def start_duplicate_detection(self):
        if not self.dup_scan_data or not self.dup_scan_data.get('files'):
            messagebox.showwarning("警告", "请先执行扫描或加载数据")
            return
        mode = 0
        if self.dup_var_hash.get(): mode |= config.DUP_BY_HASH
        if self.dup_var_size.get(): mode |= config.DUP_BY_SIZE
        if self.dup_var_name.get(): mode |= config.DUP_BY_NAME_SIM
        if self.dup_var_image.get(): mode |= config.DUP_BY_IMAGE_SIM
        if self.dup_var_video.get(): mode |= config.DUP_BY_VIDEO_SIM
        if self.dup_var_archive.get(): mode |= config.DUP_BY_ARCHIVE_SIM
        if self.dup_var_mtime.get(): mode |= config.DUP_BY_MTIME
        if mode == 0:
            messagebox.showwarning("警告", "请至少选择一种查重条件")
            return
        try:
            name_th = float(self.dup_name_th.get())
            img_th = int(self.dup_img_th.get())
            video_th = int(self.dup_video_th.get())
            archive_th = float(self.dup_archive_th.get())
            time_diff = int(self.dup_time_th.get())
        except ValueError:
            messagebox.showerror("错误", "参数格式错误")
            return
        options = {
            'mode_flags': mode,
            'name_threshold': name_th,
            'image_threshold': img_th,
            'video_threshold': video_th,
            'video_method': self.video_method.get(),
            'archive_threshold': archive_th,
            'mtime_diff': time_diff
        }
        self.create_dup_progress_window()
        self.dup_status.config(text="正在查重...")
        self.dup_stop_flag = False
        threading.Thread(target=self._duplicate_detection_worker, args=(options,), daemon=True).start()

    def _duplicate_detection_worker(self, options):
        def progress_callback(current, total, msg):
            if self.dup_progress_win and self.dup_progress_label and self.dup_progress_bar:
                self.root.after(0, lambda: self._update_dup_progress(current, total, msg))
        engine = DuplicateEngine(self.dup_scan_data['files'], options)
        self.dup_engine = engine
        groups = engine.find_duplicates(progress_callback)
        self.root.after(0, lambda: self._on_duplicate_done(groups, engine.stop_flag))

    def _update_dup_progress(self, current, total, msg):
        if self.dup_progress_label:
            self.dup_progress_label.config(text=f"{msg} ({current}/{total})")
        if self.dup_progress_bar:
            self.dup_progress_bar['maximum'] = total
            self.dup_progress_bar['value'] = current

    def _on_duplicate_done(self, groups, stopped):
        if self.dup_progress_win:
            self.dup_progress_win.destroy()
            self.dup_progress_win = None
        if stopped or self.dup_stop_flag:
            self.dup_status.config(text="查重已中止")
            return
        self.dup_groups = groups
        self.dup_status.config(text=f"发现 {len(groups)} 个重复组")
        self.dup_tree.delete(*self.dup_tree.get_children())
        self.dup_check_vars.clear()
        self.dup_selected_nodes.clear()
        self.dup_keep_index.clear()

        self._pending_dup_insert = []
        folder_total = {}
        if self.dup_scan_data:
            for f in self.dup_scan_data['files']:
                folder = os.path.dirname(f['path'])
                folder_total[folder] = folder_total.get(folder, 0) + 1

        for group in groups:
            group_text = self._get_group_summary(group)
            group_data = {
                'text': group_text,
                'open': True,
                'tags': ('group',),
                'values': ('', ''),
                'children': []
            }
            folder_map = defaultdict(list)
            for f in group:
                folder = os.path.dirname(f['path'])
                folder_map[folder].append(f)
            for folder, files in folder_map.items():
                total_in_folder = folder_total.get(folder, len(files))
                if len(files) >= 3 and len(files) > total_in_folder * 0.5:
                    folder_data = {
                        'text': f"📁 {folder}",
                        'open': False,
                        'tags': ('folder',),
                        'values': ('文件夹', folder),
                        'children': self._build_folder_children(folder, files)
                    }
                    group_data['children'].append(folder_data)
                else:
                    for f in files:
                        group_data['children'].append(self._build_file_node(folder, f))
            group_data['children'].append({'text': '', 'tags': ('separator',), 'values': ('', '')})
            self._pending_dup_insert.append(group_data)

        self._insert_dup_batch(0)

    def _build_folder_children(self, folder_path, files):
        children = []
        sub_folders = defaultdict(list)
        file_list = []
        for f in files:
            rel = os.path.relpath(f['path'], folder_path)
            if os.sep in rel:
                sub_folders[rel.split(os.sep)[0]].append(f)
            else:
                file_list.append(f)
        for sub, sub_files in sub_folders.items():
            sub_path = os.path.join(folder_path, sub)
            children.append({
                'text': f"📁 {sub}",
                'open': False,
                'tags': ('folder',),
                'values': ('文件夹', sub_path),
                'children': self._build_folder_children(sub_path, sub_files)
            })
        for i, f in enumerate(file_list):
            children.append(self._build_file_node(folder_path, f, i == len(file_list)-1 and not sub_folders))
        return children

    def _build_file_node(self, folder_path, f, is_last=True):
        name = os.path.basename(f['path'])
        ext = os.path.splitext(name)[1]
        size = utils.format_size(f['size'])
        prefix = "└─ " if is_last else "├─ "
        # 初始显示未勾选状态，复选框在最前面
        return {
            'text': f"☐ {prefix}{name} ({size})",
            'tags': ('file',),
            'values': (ext, f['path']),
            'path': f['path'],
            'size': f['size'],
            'mtime': f.get('mtime', 0)
        }

    def _insert_dup_batch(self, start_index, batch_size=2):
        if start_index >= len(self._pending_dup_insert):
            self.dup_tree.tag_configure("separator", background="#f0f0f0")
            self.save_duplicate_cache()
            self.dup_engine = None
            self._pending_dup_insert = None
            return
        end_index = min(start_index + batch_size, len(self._pending_dup_insert))
        for i in range(start_index, end_index):
            self._insert_node_recursive("", self._pending_dup_insert[i])
        self.root.update_idletasks()
        # 增加间隔到 50ms，减轻滚动时的绘制压力
        self.dup_insert_batch_id = self.root.after(50, lambda: self._insert_dup_batch(end_index, batch_size))

    def _insert_node_recursive(self, parent_id, node_data):
        item_id = self.dup_tree.insert(parent_id, "end",
                                       text=node_data['text'],
                                       open=node_data.get('open', False),
                                       tags=node_data['tags'],
                                       values=node_data['values'])
        if 'path' in node_data:
            self.dup_check_vars[item_id] = {
                "path": node_data['path'],
                "var": tk.BooleanVar(value=False),
                "size": node_data.get('size', 0),
                "mtime": node_data.get('mtime', 0)
            }
            self.dup_tree.set(item_id, "path", node_data['path'])
        for child in node_data.get('children', []):
            self._insert_node_recursive(item_id, child)

    def _get_group_summary(self, group):
        folders = list(set(os.path.dirname(f['path']) for f in group))
        if len(folders) == 1:
            return f"📁 {folders[0]} ({len(group)}个)"
        else:
            return " ⇄ ".join(f"{os.path.basename(f)}" for f in folders[:3]) + (f" +{len(folders)-3}" if len(folders) > 3 else "")

    def load_scan_data_for_duplicate(self):
        path = filedialog.askopenfilename(title="选择扫描结果文件", filetypes=[("JSON 文件", "*.json")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.dup_scan_data = data
            self._update_dup_ui_after_scan()
            messagebox.showinfo("成功", f"已加载 {len(data.get('files', []))} 个文件")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {e}")

    def save_duplicate_cache(self):
        if not self.dup_groups:
            return
        cache = {"groups": self.dup_groups, "selected": list(self.dup_selected_nodes)}
        try:
            with open(config.DUPLICATE_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False)
        except:
            pass

    def dup_keep_one(self):
        sel = self.dup_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选中一个重复组内的任意节点")
            return
        group_id = sel[0]
        while group_id and "group" not in self.dup_tree.item(group_id, "tags"):
            group_id = self.dup_tree.parent(group_id)
        if not group_id:
            return

        file_items = self._get_all_file_items_in_group(group_id)
        if not file_items:
            messagebox.showinfo("提示", "该组没有文件")
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("保留一份 - 选择保留规则")
        dlg.geometry("350x280")
        dlg.configure(bg="#f5f7fa")
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="请选择优先保留的文件规则：", bg="#f5f7fa", font=self.bold_font).pack(pady=10)
        rule_var = tk.StringVar(value="mtime_oldest")
        rules = [
            ("修改时间最早 (最旧)", "mtime_oldest"),
            ("修改时间最晚 (最新)", "mtime_newest"),
            ("文件最大", "size_largest"),
            ("文件最小", "size_smallest"),
            ("路径字母顺序 (A-Z)", "path_asc"),
        ]
        for text, value in rules:
            tk.Radiobutton(dlg, text=text, variable=rule_var, value=value,
                           bg="#f5f7fa", font=self.base_font, selectcolor="#f5f7fa").pack(anchor=tk.W, padx=20, pady=2)

        def apply():
            rule = rule_var.get()
            self._apply_keep_one_rule(group_id, file_items, rule)
            dlg.destroy()

        tk.Button(dlg, text="确定", command=apply, bg="#ffb6c1", font=self.button_font, padx=12, pady=4).pack(pady=15)
        dlg.bind("<Escape>", lambda e: dlg.destroy())

    def _get_all_file_items_in_group(self, group_id):
        result = []
        def recurse(parent):
            for child in self.dup_tree.get_children(parent):
                tags = self.dup_tree.item(child, "tags")
                if "file" in tags:
                    result.append(child)
                else:
                    recurse(child)
        recurse(group_id)
        return result

    def _apply_keep_one_rule(self, group_id, file_items, rule):
        files_info = []
        for item in file_items:
            info = self.dup_check_vars.get(item, {})
            files_info.append({
                'item': item,
                'path': info.get('path', ''),
                'size': info.get('size', 0),
                'mtime': info.get('mtime', 0)
            })
        if not files_info:
            return

        if rule == "mtime_oldest":
            sorted_files = sorted(files_info, key=lambda x: x['mtime'])
        elif rule == "mtime_newest":
            sorted_files = sorted(files_info, key=lambda x: x['mtime'], reverse=True)
        elif rule == "size_largest":
            sorted_files = sorted(files_info, key=lambda x: x['size'], reverse=True)
        elif rule == "size_smallest":
            sorted_files = sorted(files_info, key=lambda x: x['size'])
        elif rule == "path_asc":
            sorted_files = sorted(files_info, key=lambda x: x['path'])
        else:
            sorted_files = files_info

        keep_item = sorted_files[0]['item']
        for f in files_info:
            self._set_node_check(f['item'], True)
        self._set_node_check(keep_item, False)

    def dup_delete_selected(self):
        if not self.dup_selected_nodes:
            messagebox.showinfo("提示", "没有勾选任何文件")
            return
        count = len(self.dup_selected_nodes)
        if not messagebox.askyesno("确认删除", f"确定删除选中的 {count} 个文件吗？\n这将同时从项目中移除这些文件的哈希记录。"):
            return

        deleted_paths = set(self.dup_selected_nodes)
        failed_files = []
        for p in deleted_paths:
            try:
                norm_path = os.path.normpath(p)
                if os.path.exists(norm_path):
                    utils.safe_delete([norm_path])
                else:
                    raise FileNotFoundError(f"文件不存在: {norm_path}")
            except Exception as e:
                failed_files.append(p)

        if failed_files:
            messagebox.showerror("删除失败", f"以下文件删除失败：\n" + "\n".join(failed_files))

        all_projects = (self.projects + self.secondary_projects +
                        self.cache_projects + self.cache_secondary)
        for proj in all_projects:
            if "full_hashes" in proj:
                new_hashes = {}
                for rel, h in proj["full_hashes"].items():
                    abs_path = os.path.join(proj.get("address", ""), rel)
                    if abs_path not in deleted_paths:
                        new_hashes[rel] = h
                proj["full_hashes"] = new_hashes

        for path in list(self.file_hash_cache.keys()):
            if path in deleted_paths:
                del self.file_hash_cache[path]
        for path in list(self.file_size_cache.keys()):
            if path in deleted_paths:
                del self.file_size_cache[path]
        self.project_size_cache.clear()
        self.project_hash_cache.clear()

        self.save_projects()
        self.save_scan_cache()

        self.dup_selected_nodes.clear()
        if self.dup_scan_data:
            remaining_files = [f for f in self.dup_scan_data['files'] if f['path'] not in deleted_paths]
            self.dup_scan_data['files'] = remaining_files
            if remaining_files:
                self.start_duplicate_detection()
            else:
                self.dup_groups = []
                self.dup_tree.delete(*self.dup_tree.get_children())
                self.dup_status.config(text="无文件")
                self._update_preview()

    def dup_cancel_selection(self):
        for item in self.dup_tree.get_children(""):
            self._set_node_check(item, False)
        self.dup_selected_nodes.clear()
