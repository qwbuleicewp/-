# ============================================================
# 模块：扫描对话框及扫描流程 (scan_dialog.py) —— 路径持久化
# ============================================================
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import config
import utils
from scanner import UnifiedScanner

class ScanDialogMixin:
    def toggle_scan_dialog(self):
        if self.scan_dialog and self.scan_dialog.winfo_exists():
            self.scan_dialog.destroy()
            self.scan_dialog = None
        else:
            self.show_scan_dialog()

    def show_scan_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("扫描路径设置")
        win.geometry("800x650")
        win.configure(bg="#f5f7fa")
        self.scan_dialog = win

        # 关闭时保存路径
        def on_close():
            self._save_paths_from_dialog()
            setattr(self, 'scan_dialog', None)
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        win.bind("<Escape>", lambda e: on_close())

        # 左右分栏
        container = tk.Frame(win, bg="#f5f7fa")
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

        # ===== 主缓存路径 =====
        left_frame = tk.Frame(container, bg="#f5f7fa")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=2)
        left_frame.rowconfigure(1, weight=1)

        tk.Label(left_frame, text="主缓存扫描路径", bg="#f5f7fa", font=self.bold_font, fg="#000000").pack(pady=2)
        main_list_frame = tk.Frame(left_frame, bg="#f5f7fa")
        main_list_frame.pack(fill=tk.BOTH, expand=True)
        scroll1 = tk.Scrollbar(main_list_frame)
        self.main_lb = tk.Listbox(main_list_frame, yscrollcommand=scroll1.set, height=8,
                                  font=self.base_font, fg="#000000")
        scroll1.config(command=self.main_lb.yview)
        scroll1.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for d in getattr(self, 'main_scan_paths', []):
            self.main_lb.insert(tk.END, d)

        main_btn_frame = tk.Frame(left_frame, bg="#f5f7fa")
        main_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(main_btn_frame, text="添加主路径", command=lambda: self._add_path(self.main_lb),
                  bg="#ffb6c1", fg="#000000", font=self.button_font, padx=8, pady=2,
                  relief="flat").pack(side=tk.LEFT, padx=2)
        tk.Button(main_btn_frame, text="删除选中", command=lambda: self._del_path(self.main_lb),
                  bg="#ffb6c1", fg="#000000", font=self.button_font, padx=8, pady=2,
                  relief="flat").pack(side=tk.LEFT, padx=2)

        # ===== 副缓存路径 =====
        right_frame = tk.Frame(container, bg="#f5f7fa")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        right_frame.rowconfigure(1, weight=1)

        tk.Label(right_frame, text="副缓存扫描路径", bg="#f5f7fa", font=self.bold_font, fg="#000000").pack(pady=2)
        sec_list_frame = tk.Frame(right_frame, bg="#f5f7fa")
        sec_list_frame.pack(fill=tk.BOTH, expand=True)
        scroll2 = tk.Scrollbar(sec_list_frame)
        self.sec_lb = tk.Listbox(sec_list_frame, yscrollcommand=scroll2.set, height=8,
                                 font=self.base_font, fg="#000000")
        scroll2.config(command=self.sec_lb.yview)
        scroll2.pack(side=tk.RIGHT, fill=tk.Y)
        self.sec_lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for d in getattr(self, 'secondary_scan_paths', []):
            self.sec_lb.insert(tk.END, d)

        sec_btn_frame = tk.Frame(right_frame, bg="#f5f7fa")
        sec_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(sec_btn_frame, text="添加副路径", command=lambda: self._add_path(self.sec_lb),
                  bg="#ffb6c1", fg="#000000", font=self.button_font, padx=8, pady=2,
                  relief="flat").pack(side=tk.LEFT, padx=2)
        tk.Button(sec_btn_frame, text="删除选中", command=lambda: self._del_path(self.sec_lb),
                  bg="#ffb6c1", fg="#000000", font=self.button_font, padx=8, pady=2,
                  relief="flat").pack(side=tk.LEFT, padx=2)

        # 自动填充规则
        auto_frame = tk.Frame(win, bg="#f5f7fa")
        auto_frame.pack(fill=tk.X, padx=10, pady=(10,0))
        tk.Label(auto_frame, text="自动填充规则:", bg="#f5f7fa", font=self.bold_font, fg="#000000").pack(anchor=tk.W)
        match_name_var = tk.BooleanVar(value=True)
        match_tag_var = tk.BooleanVar(value=True)
        folder_desc_var = tk.BooleanVar(value=True)
        tk.Checkbutton(auto_frame, text="根据已有项目正名/别名匹配 (大小写不敏感)",
                       variable=match_name_var, bg="#f5f7fa", font=self.base_font,
                       fg="#000000", selectcolor="#f5f7fa").pack(anchor=tk.W)
        tk.Checkbutton(auto_frame, text="根据标签及别名自动添加标签",
                       variable=match_tag_var, bg="#f5f7fa", font=self.base_font,
                       fg="#000000", selectcolor="#f5f7fa").pack(anchor=tk.W)
        tk.Checkbutton(auto_frame, text="文件夹名作为介绍",
                       variable=folder_desc_var, bg="#f5f7fa", font=self.base_font,
                       fg="#000000", selectcolor="#f5f7fa").pack(anchor=tk.W)

        # 开始扫描按钮
        def run():
            self._save_paths_from_dialog()
            self._scan_match_name = match_name_var.get()
            self._scan_match_tag = match_tag_var.get()
            self._scan_folder_desc = folder_desc_var.get()
            self.save_config()
            win.destroy()
            self.start_unified_scan()

        tk.Button(win, text="开始扫描", command=run, bg="#ffb6c1", fg="#000000",
                  font=self.button_font, padx=12, pady=4, relief="flat").pack(pady=10)

    def _save_paths_from_dialog(self):
        # 从 Listbox 读取当前内容并更新到属性
        if hasattr(self, 'main_lb') and self.main_lb.winfo_exists():
            self.main_scan_paths = list(self.main_lb.get(0, tk.END))
        if hasattr(self, 'sec_lb') and self.sec_lb.winfo_exists():
            self.secondary_scan_paths = list(self.sec_lb.get(0, tk.END))
        self.save_config()

    def _add_path(self, listbox):
        p = filedialog.askdirectory(parent=self.scan_dialog)
        if p:
            listbox.insert(tk.END, p)

    def _del_path(self, listbox):
        sel = listbox.curselection()
        if sel:
            listbox.delete(sel[0])

    # ---------- 二代统一扫描（保持不变） ----------
    def start_unified_scan(self):
        all_paths = getattr(self, 'main_scan_paths', []) + getattr(self, 'secondary_scan_paths', [])
        if not all_paths:
            messagebox.showwarning("警告", "请先设置至少一个扫描路径")
            return
        if self.unified_scanner and not getattr(self.unified_scanner, 'stop_flag', True):
            self.stop_scan()
            return
        self.create_scan_progress_window()
        self.scan_thread = threading.Thread(target=self._unified_scan_worker, daemon=True)
        self.scan_thread.start()

    def create_scan_progress_window(self):
        if self.scan_progress_win and self.scan_progress_win.winfo_exists():
            self.scan_progress_win.destroy()
        win = tk.Toplevel(self.root)
        win.title("扫描进度")
        win.geometry("500x400")
        win.configure(bg="#f5f7fa")
        win.protocol("WM_DELETE_WINDOW", self.on_scan_window_close)
        tk.Label(win, text="统一扫描", font=self.bold_font, bg="#f5f7fa").pack(pady=10)
        self.scan_log_text = scrolledtext.ScrolledText(win, height=12, state='normal')
        self.scan_log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.scan_progress_bar = ttk.Progressbar(win, mode='indeterminate')
        self.scan_progress_bar.pack(fill=tk.X, padx=10, pady=5)
        self.scan_progress_bar.start()
        btn_frame = tk.Frame(win, bg="#f5f7fa")
        btn_frame.pack(pady=5)
        self.scan_button = tk.Button(btn_frame, text="停止扫描", command=self.stop_scan,
                                     bg="#ffb6c1", font=self.button_font, padx=8)
        self.scan_button.pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="后台运行", command=self.hide_scan_window,
                  bg="#d3d3d3", font=self.button_font, padx=8).pack(side=tk.LEFT, padx=5)
        self.scan_progress_win = win
        self.log_to_scan_window("准备扫描...")

    def on_scan_window_close(self):
        if self.scan_progress_win:
            self.scan_progress_win.destroy()
            self.scan_progress_win = None

    def hide_scan_window(self):
        self.on_scan_window_close()

    def close_scan_progress_window(self):
        if hasattr(self, 'scan_auto_close_id') and self.scan_auto_close_id:
            self.root.after_cancel(self.scan_auto_close_id)
        if self.scan_progress_win and self.scan_progress_win.winfo_exists():
            self.scan_progress_win.destroy()
            self.scan_progress_win = None

    def stop_scan(self):
        if self.unified_scanner:
            self.unified_scanner.stop()
        self.log_to_scan_window("正在停止扫描...")
        if self.scan_button and self.scan_button.winfo_exists():
            self.scan_button.config(text="开始扫描", command=self.start_unified_scan)

    def log_to_scan_window(self, msg):
        if self.scan_progress_win and self.scan_log_text:
            self.scan_log_text.insert(tk.END, msg + "\n")
            self.scan_log_text.see(tk.END)

    def _unified_scan_worker(self):
        self.root.after(0, lambda: self.update_tray_icon(True))
        if self.power_mode == config.POWER_MODE_LOW:
            self.power_manager.set_mode(config.POWER_MODE_LOW)

        def log_cb(msg):
            self.root.after(0, lambda: self.log_to_scan_window(msg))

        def prog_cb(msg):
            self.root.after(0, lambda: self.log_to_scan_window(msg))

        def complete_cb(result, stopped):
            self.root.after(0, lambda: self._on_scan_complete(result, stopped))

        all_paths = getattr(self, 'main_scan_paths', []) + getattr(self, 'secondary_scan_paths', [])
        scanner = UnifiedScanner(
            all_paths, log_cb, prog_cb, complete_cb,
            self.project_size_cache, self.project_hash_cache,
            self.file_size_cache, self.file_hash_cache
        )
        self.unified_scanner = scanner
        scanner.scan()

    def _on_scan_complete(self, result, stopped):
        if self.scan_progress_win and self.scan_progress_win.winfo_exists():
            self.scan_progress_bar.stop()
            self.scan_thread = None   # 添加这一行

        self.save_config()
        if not stopped:
            self.dup_scan_data = {"files": result["all_files"], "scan_time": result["scan_time"]}
            match_name = getattr(self, '_scan_match_name', True)
            match_tag = getattr(self, '_scan_match_tag', True)
            folder_desc = getattr(self, '_scan_folder_desc', True)
            main_paths = getattr(self, 'main_scan_paths', [])
            sec_paths = getattr(self, 'secondary_scan_paths', [])

            for proj in result["projects"]:
                proj_path = proj["path"]
                target_cache = "main"
                for p in main_paths:
                    if proj_path.startswith(p):
                        target_cache = "main"
                        break
                else:
                    for p in sec_paths:
                        if proj_path.startswith(p):
                            target_cache = "secondary"
                            break

                existing = next((p for p in (
                    self.cache_projects if target_cache == "main" else self.cache_secondary
                ) if p.get("address") == proj_path), None)
                if existing:
                    existing["full_hashes"] = proj["hashes"]
                    existing["address"] = proj_path
                else:
                    name = proj["name"]
                    matched_name = name
                    matched_alias = ""
                    if match_name:
                        for p in (self.projects + self.cache_projects +
                                  self.secondary_projects + self.cache_secondary):
                            if (p.get("name", "").lower() in name.lower() or
                                (p.get("alias", "") and p["alias"].lower() in name.lower())):
                                matched_name = p.get("name", name)
                                matched_alias = p.get("alias", "")
                                break
                    tags = []
                    if match_tag:
                        name_lower = name.lower()
                        for tag in (self.all_tags_primary | self.all_tags_secondary |
                                    self.preset_tags):
                            if tag.lower() in name_lower:
                                tags.append(tag)
                        for alias, tag in self.alias_map.items():
                            if alias in name_lower:
                                tags.append(tag)
                    desc = name if folder_desc else ""
                    new_id = utils.get_next_id([
                        self.projects, self.cache_projects,
                        self.secondary_projects, self.cache_secondary
                    ])
                    new_proj = {
                        "id": new_id,
                        "name": matched_name,
                        "alias": matched_alias,
                        "description": desc,
                        "location": config.DEFAULT_LOCATION,
                        "address": proj_path,
                        "tags": tags,
                        "image": None,
                        "full_hashes": proj["hashes"]
                    }
                    if target_cache == "main":
                        self.cache_projects.append(new_proj)
                        for t in tags:
                            self.all_tags_primary.add(t)
                    else:
                        self.cache_secondary.append(new_proj)
                        for t in tags:
                            self.all_tags_secondary.add(t)

            self.save_projects()
            self.save_scan_cache()
            self.log_to_scan_window(
                f"扫描完成：项目 {len(result['projects'])} 个，文件 {len(result['all_files'])} 个")
        else:
            self.log_to_scan_window("扫描已中止")

        self.unified_scanner = None
        self.root.after(0, lambda: self.update_tray_icon(False))
        if not stopped and self.scan_progress_win and self.scan_progress_win.winfo_exists():
            self.scan_auto_close_id = self.root.after(3000, self.close_scan_progress_window)

        if self.current_view == "duplicate":
            self.root.after(0, self._update_dup_ui_after_scan)
        else:
            self.update_data_and_redraw()
