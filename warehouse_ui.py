# ============================================================
# 模块：仓库主界面 UI (warehouse_ui.py) —— 完整修正版
# ============================================================
import os
import tkinter as tk
from tkinter import ttk, messagebox
import config
import utils

class WarehouseUIMixin:
    def init_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background="#f5f7fa", foreground="#000000")
        style.configure('TLabel', background="#f5f7fa", font=self.base_font)
        style.configure("Large.TButton", font=self.button_font, padding=(12, 6),
                        relief="flat", background="#ffb6c1")
        style.map("Large.TButton", background=[('active', '#ff9eb5')])
        style.configure("ActiveView.TButton", font=self.button_font, padding=(12, 6),
                        relief="flat", background="#d3d3d3")

        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=8)

        left_btns = ttk.Frame(top_frame)
        left_btns.pack(side=tk.LEFT)

        ttk.Button(left_btns, text="📂 扫描", command=self.start_unified_scan,
                   style="Large.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(left_btns, text="⚙️ 扫描路径", command=self.toggle_scan_dialog,
                   style="Large.TButton").pack(side=tk.LEFT, padx=4)
        ttk.Button(left_btns, text="🏷️ 别名管理", command=self.show_alias_dialog,
                   style="Large.TButton").pack(side=tk.LEFT, padx=4)

        self.view_mode_btn = ttk.Button(left_btns, text="📋 列表模式", command=self.toggle_view_mode,
                                        style="Large.TButton")
        self.view_mode_btn.pack(side=tk.LEFT, padx=(10, 4))

        self.more_btn = ttk.Menubutton(left_btns, text="▼ 更多", style="Large.TButton")
        self.more_btn.pack(side=tk.LEFT, padx=4)
        more_menu = tk.Menu(self.more_btn, tearoff=0, font=self.base_font,
                            bg="#ffffff", fg="#000000")
        more_menu.add_command(label="🔄 重置过滤", command=self.reset_filters)
        more_menu.add_command(label="💾 保存", command=self.save_all)
        more_menu.add_command(label="📂 加载", command=self.load_data_from_file)
        self.more_btn.configure(menu=more_menu)

        self.count_frame = ttk.Frame(top_frame)
        self.count_frame.pack(side=tk.LEFT, expand=True, padx=20)
        self.count_main_label = tk.Label(self.count_frame, text="", font=self.bold_font,
                                         fg="#000000", bg="#f5f7fa")
        self.count_main_label.pack(side=tk.LEFT)
        self.count_plus_label = tk.Label(self.count_frame, text=" + ", font=self.base_font,
                                         fg="#888888", bg="#f5f7fa")
        self.count_plus_label.pack(side=tk.LEFT)
        self.count_cache_label = tk.Label(self.count_frame, text="", font=self.base_font,
                                          fg="#888888", bg="#f5f7fa")
        self.count_cache_label.pack(side=tk.LEFT)

        view_frame = ttk.Frame(top_frame)
        view_frame.pack(side=tk.RIGHT)
        self.view_btns = {}
        views = [("warehouse", "🏠 主仓库"), ("secondary", "📦 副仓库"),
                 ("cache", "🗃️ 主缓存"), ("cacheSecondary", "📁 副缓存"),
                 ("duplicate", "🔍 查重")]
        for v, text in views:
            btn = ttk.Button(view_frame, text=text, command=lambda v=v: self.switch_view(v),
                             style="Large.TButton")
            btn.pack(side=tk.LEFT, padx=4)
            self.view_btns[v] = btn

        self.main_frame = tk.Frame(self.root, bg="#ffffff")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.header_canvas = tk.Canvas(self.main_frame, height=config.HEADER_ROW_HEIGHT,
                                       bg="#f0f3f8")
        self.header_canvas.pack(fill=tk.X, pady=0)
        self.filter_canvas = tk.Canvas(self.main_frame, height=config.FILTER_ROW_HEIGHT,
                                       bg="#f0f3f8")
        self.filter_canvas.pack(fill=tk.X, pady=0)

        self.data_container = tk.Frame(self.main_frame, bg="#ffffff")
        self.data_container.pack(fill=tk.BOTH, expand=True)
        self.data_canvas = tk.Canvas(self.data_container, bg="#ffffff", highlightthickness=0)
        self.data_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.duplicate_frame = tk.Frame(self.data_container, bg="#ffffff")

        self.data_canvas.bind("<Configure>", self._on_canvas_configure)
        self.data_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.header_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.filter_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.data_canvas.bind("<ButtonRelease-1>", self._on_canvas_click)
        self.draw_header()
        self.draw_filter_row()
        self.root.bind("<Configure>", self.on_window_resize)

    def toggle_view_mode(self):
        if self.warehouse_view_mode == config.VIEW_MODE_TABLE:
            self.warehouse_view_mode = config.VIEW_MODE_THUMBNAIL
            self.view_mode_btn.config(text="📋 列表模式")
        else:
            self.warehouse_view_mode = config.VIEW_MODE_TABLE
            self.view_mode_btn.config(text="🖼️ 缩略图模式")
        self.data_canvas.yview_moveto(0)
        self.update_data_and_redraw()

    # ---------- 表头 ----------
    def draw_header(self):
        self.header_canvas.delete("all")
        if self.current_view not in ("warehouse", "secondary", "cache", "cacheSecondary") or self.warehouse_view_mode == config.VIEW_MODE_THUMBNAIL:
            return
        x = 0
        for i, col in enumerate(config.COLUMNS):
            width = self.col_widths[i]
            rect = self.header_canvas.create_rectangle(
                x, 0, x+width, config.HEADER_ROW_HEIGHT,
                fill="#eef2f6", outline="#d0d7de", width=1)
            if i < len(config.COLUMNS) - 1:
                self.header_canvas.create_line(
                    x+width-1, 0, x+width-1, config.HEADER_ROW_HEIGHT,
                    fill="#d0d7de", width=1)
            display = col["name"]
            if col["key"] in ("num", "name") and col["key"] == self.sort_column:
                display += " ▲" if self.sort_asc else " ▼"
            text_id = self.header_canvas.create_text(
                x+width//2, config.HEADER_ROW_HEIGHT//2,
                text=display, font=self.bold_font, fill="#000000")
            if col["key"] in ("num", "name"):
                for item in (rect, text_id):
                    self.header_canvas.tag_bind(
                        item, "<Button-1>",
                        lambda e, k=col["key"]: self.sort_by(k))
            x += width

    def draw_filter_row(self):
        for child in self.filter_canvas.winfo_children():
            child.destroy()
        self.filter_canvas.delete("all")
        self.filter_widgets = {}
        x = 0
        for i, col in enumerate(config.COLUMNS):
            width = self.col_widths[i]
            self.filter_canvas.create_rectangle(x, 0, x+width, config.FILTER_ROW_HEIGHT,
                                                fill="#f8fafc", outline="#d0d7de", width=1)
            if i < len(config.COLUMNS) - 1:
                self.filter_canvas.create_line(x+width-1, 0, x+width-1, config.FILTER_ROW_HEIGHT,
                                               fill="#d0d7de", width=1)
            if col["key"] in ("pic", "num"):
                if i == 0:
                    jump_frame = tk.Frame(self.filter_canvas, bg="#f8fafc")
                    jump_frame.place(x=x+5, y=2, width=width-10,
                                     height=config.FILTER_ROW_HEIGHT-4)
                    ttk.Label(jump_frame, text="编号:", font=self.bold_font,
                              background="#f8fafc").pack(side=tk.LEFT, padx=2)
                    self.jump_entry = ttk.Entry(jump_frame, width=8, justify="center")
                    self.jump_entry.pack(side=tk.LEFT, padx=2)
                    self.jump_entry.bind("<Return>", self.jump_to_id)
                    self.filter_widgets["jump"] = jump_frame
            elif col["key"] in ("name", "tags", "desc", "loc"):
                cb = ttk.Combobox(self.filter_canvas, state="normal")
                cb.place(x=x+2, y=2, width=width-4, height=config.FILTER_ROW_HEIGHT-4)
                cb.bind("<<ComboboxSelected>>", lambda e, k=col["key"]: self.on_filter_change(k))
                cb.bind("<Return>", lambda e, k=col["key"]: self.on_filter_change(k))
                cb.bind("<ButtonPress-1>",
                        lambda e, k=col["key"], cb=cb: self._prepare_and_show_dropdown(k, cb))
                self.filter_widgets[col["key"]] = cb
            x += width

    def _prepare_and_show_dropdown(self, col_key, cb):
        self.ensure_filter_menu(col_key)
        cb.after(10, lambda: cb.event_generate('<Down>'))

    def _on_canvas_configure(self, event):
        self.redraw_visible_rows()

    def _on_mousewheel(self, event):
        total_height = self.total_items * config.ROW_HEIGHT
        canvas_height = self.data_canvas.winfo_height()
        if total_height <= canvas_height:
            return
        delta = event.delta if event.delta else (120 if event.num == 4 else -120)
        yview = self.data_canvas.yview()
        if delta > 0 and yview[0] <= 0:
            return
        if delta < 0 and yview[1] >= 1:
            return
        self.data_canvas.yview_scroll(int(-delta / 60), "units")
        self.redraw_visible_rows()

    def on_window_resize(self, event):
        if event.widget == self.root:
            if self.resize_after_id:
                self.root.after_cancel(self.resize_after_id)
            self.resize_after_id = self.root.after(100, self._delayed_resize)

    def _delayed_resize(self):
        self.update_column_widths()
        self.resize_after_id = None

    def update_column_widths(self):
        width = self.main_frame.winfo_width()
        if width < 100:
            return
        fixed_width = sum(c["width"] for c in config.COLUMNS if not c["stretch"])
        stretch_width = width - fixed_width
        stretch_cols = [c for c in config.COLUMNS if c["stretch"]]
        if stretch_cols:
            total_stretch = sum(c["width"] for c in stretch_cols)
            ratio = stretch_width / total_stretch if total_stretch > 0 else 1
            new_widths = []
            for c in config.COLUMNS:
                if c["stretch"]:
                    new_widths.append(int(c["width"] * ratio))
                else:
                    new_widths.append(c["width"])
        else:
            new_widths = [c["width"] for c in config.COLUMNS]
        new_widths = [max(20, w) for w in new_widths]
        if new_widths != self.col_widths:
            self.col_widths = new_widths
            self.draw_header()
            self.draw_filter_row()
            self.redraw_visible_rows()

    def jump_to_id(self, event=None):
        try:
            target_id = int(self.jump_entry.get())
        except:
            return
        for idx, p in enumerate(self.filtered_list):
            if p["id"] == target_id:
                y = idx * config.ROW_HEIGHT
                self.data_canvas.yview_moveto(y / max(1, self.total_items * config.ROW_HEIGHT))
                self.redraw_visible_rows()
                return
        messagebox.showinfo("提示", f"未找到编号为 {target_id} 的项目")

    def sort_by(self, col_key):
        if self.sort_column == col_key:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_column = col_key
            self.sort_asc = True
        self.update_data_and_redraw()

    def on_filter_change(self, col_name):
        if col_name == "name":
            self.filter_name = self.filter_widgets["name"].get()
        elif col_name == "tags":
            self.filter_tags = self.filter_widgets["tags"].get()
        elif col_name == "desc":
            self.filter_desc = self.filter_widgets["desc"].get()
        elif col_name == "loc":
            self.filter_location = self.filter_widgets["loc"].get()
        self.update_data_and_redraw()

    def reset_filters(self):
        self.filter_name = self.filter_tags = self.filter_desc = self.filter_location = ""
        for key in ("name", "tags", "desc", "loc"):
            if key in self.filter_widgets:
                self.filter_widgets[key].set("")
        self.update_data_and_redraw()

    def ensure_filter_menu(self, col_name):
        if self.filter_menu_dirty:
            self._rebuild_filter_menus()
        if col_name in self.filter_widgets:
            self.filter_widgets[col_name]['values'] = self.filter_menu_cache.get(col_name, [])

    def _rebuild_filter_menus(self):
        current_list = self.get_current_list()
        names = set()
        tags = set()
        descs = set()
        locs = set()
        for p in current_list:
            names.add(p.get("name", ""))
            if p.get("alias"):
                names.add(p.get("alias", ""))
            for t in p.get("tags", []):
                tags.add(t)
            descs.add(p.get("description", ""))
            locs.add(p.get("location", ""))
        self.filter_menu_cache = {
            "name": sorted(names), "tags": sorted(tags),
            "desc": sorted(descs), "loc": sorted(locs)
        }
        self.filter_menu_dirty = False

    def get_current_list(self):
        if self.current_view == "warehouse":
            return self.projects
        elif self.current_view == "secondary":
            return self.secondary_projects
        elif self.current_view == "cache":
            return self.cache_projects
        elif self.current_view == "cacheSecondary":
            return self.cache_secondary
        else:
            return []

    def get_filtered_list(self):
        lst = self.get_current_list()
        if self.filter_name:
            fn = self.filter_name.lower()
            lst = [p for p in lst if fn in p.get("name", "").lower() or fn in p.get("alias", "").lower()]
        if self.filter_tags:
            ft = self.filter_tags.lower()
            lst = [p for p in lst if any(ft in t.lower() for t in p.get("tags", []))]
        if self.filter_desc:
            fd = self.filter_desc.lower()
            lst = [p for p in lst if fd in p.get("description", "").lower()]
        if self.filter_location:
            lst = [p for p in lst if p.get("location", "") == self.filter_location]
        if self.sort_column == "num":
            lst.sort(key=lambda p: p.get("id", 0), reverse=not self.sort_asc)
        else:
            lst.sort(key=lambda p: p.get("name", ""), reverse=not self.sort_asc)
        return lst

    def update_data_and_redraw(self):
        self.filter_menu_dirty = True
        self.filtered_list = self.get_filtered_list()
        self.total_items = len(self.filtered_list)
        canvas_width = self.data_canvas.winfo_width() or 100
        self.data_canvas.config(scrollregion=(0, 0, canvas_width,
                                              self.total_items * config.ROW_HEIGHT))
        if self.total_items == 0:
            self.data_canvas.yview_moveto(0)
        self._update_count_labels()
        self.draw_header()
        self.redraw_visible_rows()

    def _update_count_labels(self):
        if self.current_view == "warehouse":
            main_count = len(self.projects)
            cache_count = len(self.cache_projects)
            self.count_main_label.config(text=f"主仓库：{main_count}")
            self.count_cache_label.config(text=str(cache_count))
        elif self.current_view == "cache":
            main_count = len(self.projects)
            cache_count = len(self.cache_projects)
            self.count_main_label.config(text=f"主仓库：{main_count}")
            self.count_cache_label.config(text=str(cache_count))
        elif self.current_view == "secondary":
            main_count = len(self.secondary_projects)
            cache_count = len(self.cache_secondary)
            self.count_main_label.config(text=f"副仓库：{main_count}")
            self.count_cache_label.config(text=str(cache_count))
        elif self.current_view == "cacheSecondary":
            main_count = len(self.secondary_projects)
            cache_count = len(self.cache_secondary)
            self.count_main_label.config(text=f"副仓库：{main_count}")
            self.count_cache_label.config(text=str(cache_count))
        else:
            self.count_main_label.config(text="查重视图")
            self.count_cache_label.config(text="")

    def redraw_visible_rows(self):
        if self.redraw_after_id:
            self.root.after_cancel(self.redraw_after_id)
        self.redraw_after_id = self.root.after(100, self._do_redraw)

    # ---------- 核心绘制 ----------
    def _do_redraw(self):
        self.data_canvas.delete("all")
        self.row_images.clear()
        if self.total_items == 0:
            return
        canvas_height = self.data_canvas.winfo_height()
        if canvas_height <= 0:
            return

        if self.current_view in ("warehouse", "secondary") and self.warehouse_view_mode == config.VIEW_MODE_THUMBNAIL:
            self._draw_thumbnail_view()
            return

        yview = self.data_canvas.yview()
        total_height = self.total_items * config.ROW_HEIGHT
        first_row = max(0, int(yview[0] * total_height) // config.ROW_HEIGHT - config.BUFFER_ROWS)
        last_row = min(self.total_items - 1,
                       int(yview[1] * total_height) // config.ROW_HEIGHT + config.BUFFER_ROWS)

        for row_idx in range(first_row, last_row + 1):
            p = self.filtered_list[row_idx]
            y = row_idx * config.ROW_HEIGHT
            bg = "#f5f7fa" if row_idx % 2 == 0 else "#eaeef2"
            if p.get("address") and not os.path.exists(p["address"]):
                bg = "#ffcccc"

            x = 0
            for i, col in enumerate(config.COLUMNS):
                width = self.col_widths[i]
                self.data_canvas.create_rectangle(
                    x, y, x+width, y+config.ROW_HEIGHT,
                    fill=bg, outline="", tags=("cell_bg",))
                if i < len(config.COLUMNS) - 1:
                    self.data_canvas.create_line(
                        x+width-1, y, x+width-1, y+config.ROW_HEIGHT,
                        fill="#e0e6ed", tags=("grid",))
                x += width

            x = 0
            for i, col in enumerate(config.COLUMNS):
                width = self.col_widths[i]
                pid = p["id"]
                path = p.get("address", "")
                name = p.get("name", "")
                alias = p.get("alias", "")
                tags = p.get("tags", [])
                desc = p.get("description", "")
                loc = p.get("location", "")

                if col["key"] == "pic":
                    img = None
                    if p.get("image"):
                        if pid not in self.thumbnail_cache:
                            thumb = utils.base64_to_thumbnail(p["image"])
                            if thumb:
                                self.thumbnail_cache[pid] = thumb
                        img = self.thumbnail_cache.get(pid)
                    if img:
                        self.data_canvas.create_image(
                            x+width//2, y+config.ROW_HEIGHT//2, image=img, tags=("pic_content",))
                        self.row_images[row_idx] = img
                    else:
                        self.data_canvas.create_text(
                            x+width//2, y+config.ROW_HEIGHT//2,
                            text="无图", font=self.base_font, fill="#000000", tags=("pic_content",))
                    hover_rect = self.data_canvas.create_rectangle(
                        x, y, x+width, y+config.ROW_HEIGHT,
                        fill="", outline="", tags=("pic_hover",))
                    capture_rect = self.data_canvas.create_rectangle(
                        x, y, x+width, y+config.ROW_HEIGHT,
                        fill="", outline="", tags=("pic_capture",))
                    if self.current_view in ("cache", "cacheSecondary"):
                        self.data_canvas.tag_bind(capture_rect, "<Double-Button-1>",
                                                  lambda e, pid=pid, addr=path: self.upload_and_copy_address(pid, addr))
                    else:
                        self.data_canvas.tag_bind(capture_rect, "<Double-Button-1>",
                                                  lambda e, path=path: self.open_project_folder(path))
                    self._bind_hover(hover_rect, "", "#d0d0d0")

                elif col["key"] in ("num", "name", "tags", "desc", "loc"):
                    text_content = ""
                    if col["key"] == "num":
                        text_content = str(pid)
                    elif col["key"] == "name":
                        text_content = f"{name}\n{alias}" if alias else name
                    elif col["key"] == "tags":
                        text_content = ", ".join(tags)
                    elif col["key"] == "desc":
                        text_content = desc
                    elif col["key"] == "loc":
                        text_content = loc
                    self.data_canvas.create_text(
                        x+8 if col["key"] != "num" else x+width//2,
                        y+config.ROW_HEIGHT//2,
                        text=text_content, font=self.base_font, fill="#000000",
                        anchor=tk.W if col["key"] != "num" else tk.CENTER, tags=("cell_text",))
                    hover_rect = self.data_canvas.create_rectangle(
                        x, y, x+width, y+config.ROW_HEIGHT,
                        fill="", outline="", tags=("cell_hover",))
                    capture_rect = self.data_canvas.create_rectangle(
                        x, y, x+width, y+config.ROW_HEIGHT,
                        fill="", outline="", tags=("cell_capture",))
                    self.data_canvas.tag_bind(capture_rect, "<Double-Button-1>",
                                              lambda e, pid=pid: self.open_edit_dialog(pid))
                    self._bind_hover(hover_rect, "", "#d0d0d0")

                elif col["key"] == "action":
                    if self.current_view in ("cache", "cacheSecondary"):
                        btn_w = width // 2
                        cbtn = self.data_canvas.create_rectangle(x, y, x+btn_w, y+config.ROW_HEIGHT//2, fill="#e8f5e9", outline="#c8e6c9", tags=("action_bg",))
                        self.data_canvas.create_text(x+btn_w//2, y+config.ROW_HEIGHT//4, text="✅", font=('Microsoft YaHei', 15), tags=("action_text",))
                        dbtn = self.data_canvas.create_rectangle(x+btn_w, y, x+width, y+config.ROW_HEIGHT//2, fill="#ffebee", outline="#ffcdd2", tags=("action_bg",))
                        self.data_canvas.create_text(x+btn_w+btn_w//2, y+config.ROW_HEIGHT//4, text="🗑️", font=('Microsoft YaHei', 15), tags=("action_text",))
                        ebtn = self.data_canvas.create_rectangle(x, y+config.ROW_HEIGHT//2, x+width, y+config.ROW_HEIGHT, fill="#eceff1", outline="#cfd8dc", tags=("action_bg",))
                        self.data_canvas.create_text(x+width//2, y+3*config.ROW_HEIGHT//4, text="✏️", font=('Microsoft YaHei', 15), tags=("action_text",))
                        ccap = self.data_canvas.create_rectangle(x, y, x+btn_w, y+config.ROW_HEIGHT//2, fill="", outline="", tags=("action_capture",))
                        dcap = self.data_canvas.create_rectangle(x+btn_w, y, x+width, y+config.ROW_HEIGHT//2, fill="", outline="", tags=("action_capture",))
                        ecap = self.data_canvas.create_rectangle(x, y+config.ROW_HEIGHT//2, x+width, y+config.ROW_HEIGHT, fill="", outline="", tags=("action_capture",))
                        self.data_canvas.tag_bind(ccap, "<Button-1>", lambda e, pid=pid: self.confirm_to_warehouse(pid))
                        self.data_canvas.tag_bind(dcap, "<Button-1>", lambda e, pid=pid: self.delete_from_cache(pid))
                        self.data_canvas.tag_bind(ecap, "<Button-1>", lambda e, pid=pid: self.open_edit_dialog(pid))
                        self._bind_hover(cbtn, "#e8f5e9", "#c8e6c9")
                        self._bind_hover(dbtn, "#ffebee", "#ffcdd2")
                        self._bind_hover(ebtn, "#eceff1", "#cfd8dc")
                    else:
                        edit_bg = self.data_canvas.create_rectangle(x, y, x+width, y+config.ROW_HEIGHT, fill="#eceff1", outline="#cfd8dc", tags=("action_bg",))
                        self.data_canvas.create_text(x+width//2, y+config.ROW_HEIGHT//2, text="编辑", font=self.base_font, fill="#000000", tags=("action_text",))
                        ecap = self.data_canvas.create_rectangle(x, y, x+width, y+config.ROW_HEIGHT, fill="", outline="", tags=("action_capture",))
                        self.data_canvas.tag_bind(ecap, "<Button-1>", lambda e, pid=pid: self.open_edit_dialog(pid))
                        self._bind_hover(edit_bg, "#eceff1", "#cfd8dc")
                x += width

        self.data_canvas.tag_raise("pic_capture")
        self.data_canvas.tag_raise("cell_capture")
        self.data_canvas.tag_raise("action_capture")
        if self.total_items > 0:
            self.data_canvas.focus_set()

    # ---------- 缩略图模式 ----------
    def _draw_thumbnail_view(self):
        canvas_width = self.data_canvas.winfo_width()
        if canvas_width < 100:
            return

        thumb_size = 180
        padding = 20
        text_height = 110
        item_width = thumb_size + padding
        item_height = thumb_size + text_height + padding

        cols = max(1, (canvas_width - padding) // item_width)
        row_count = (self.total_items + cols - 1) // cols

        total_height = row_count * item_height + padding
        self.data_canvas.config(scrollregion=(0, 0, canvas_width, total_height))

        yview = self.data_canvas.yview()
        view_top = yview[0] * total_height
        view_bottom = yview[1] * total_height

        first_row = max(0, int(view_top // item_height) - 1)
        last_row = min(row_count - 1, int(view_bottom // item_height) + 1)

        for row_idx in range(first_row, last_row + 1):
            for col_idx in range(cols):
                item_idx = row_idx * cols + col_idx
                if item_idx >= self.total_items:
                    break
                p = self.filtered_list[item_idx]
                pid = p["id"]
                path = p.get("address", "")
                name = p.get("name", "")
                alias = p.get("alias", "")
                tags_list = p.get("tags", [])
                desc = p.get("description", "")

                bg_color = "#f0f3f7" if (row_idx + col_idx) % 2 == 0 else "#e4e8ee"
                hover_color = "#d0d6df"

                x0 = padding + col_idx * item_width
                y0 = padding + row_idx * item_height

                self.data_canvas.create_rectangle(
                    x0, y0, x0 + item_width, y0 + item_height,
                    fill=bg_color, outline="", tags=("thumb_bg",))
                hover_rect = self.data_canvas.create_rectangle(
                    x0, y0, x0 + item_width, y0 + item_height,
                    fill="", outline="", tags=("thumb_hover",))

                img_x = x0 + (item_width - thumb_size) // 2
                img_y = y0 + 10
                img = None
                if p.get("image"):
                    if pid not in self.thumbnail_cache:
                        thumb = utils.base64_to_thumbnail(p["image"], (thumb_size, thumb_size))
                        if thumb:
                            self.thumbnail_cache[pid] = thumb
                    img = self.thumbnail_cache.get(pid)
                if img:
                    self.data_canvas.create_image(
                        img_x + thumb_size//2, img_y + thumb_size//2,
                        image=img, tags=("thumb_img",))
                    self.row_images[item_idx] = img
                else:
                    self.data_canvas.create_text(
                        img_x + thumb_size//2, img_y + thumb_size//2,
                        text="无图", font=self.base_font, fill="#000000", tags=("thumb_text",))

                text_y = img_y + thumb_size + 5

                # 名称
                name_text = f"{name} ({alias})" if alias else name
                if len(name_text) > 20:
                    name_text = name_text[:17] + "..."
                tid1 = self.data_canvas.create_text(
                    img_x + thumb_size//2, text_y,
                    text=name_text, font=self.bold_font, fill="#000000",
                    anchor=tk.N, width=thumb_size, tags=("thumb_name",))

                # 简介
                desc_lines = [desc[i:i+20] for i in range(0, min(len(desc), 40), 20)] if desc else []
                if not desc_lines:
                    desc_lines = [" ", " "]
                elif len(desc_lines) == 1:
                    desc_lines.append(" ")
                line1 = desc_lines[0][:20] if desc_lines[0].strip() else " "
                line2 = desc_lines[1][:20] + ("..." if len(desc) > 40 else "")
                if not line2.strip():
                    line2 = " "
                tid2 = self.data_canvas.create_text(
                    img_x + thumb_size//2, text_y + 24,
                    text=line1, font=self.base_font, fill="#555555",
                    anchor=tk.N, width=thumb_size, tags=("thumb_desc",))
                tid3 = self.data_canvas.create_text(
                    img_x + thumb_size//2, text_y + 46,
                    text=line2, font=self.base_font, fill="#555555",
                    anchor=tk.N, width=thumb_size, tags=("thumb_desc",))

                # 标签
                tag_str = ", ".join(tags_list) if tags_list else " "
                if len(tag_str) > 30:
                    tag_str = tag_str[:27] + "..."
                tid4 = self.data_canvas.create_text(
                    img_x + thumb_size//2, text_y + 68,
                    text=tag_str, font=self.base_font, fill="#888888",
                    anchor=tk.N, width=thumb_size, tags=("thumb_tags",))

                self._bind_hover(hover_rect, "", hover_color)

                capture_rect = self.data_canvas.create_rectangle(
                    x0, y0, x0 + item_width, y0 + item_height,
                    fill="", outline="", tags=("thumb_capture",))
                self.data_canvas.tag_bind(capture_rect, "<Double-Button-1>",
                                          lambda e, x0=x0, y0=y0, item_width=item_width,
                                                 thumb_size=thumb_size, text_height=text_height,
                                                 pid=pid, path=path:
                                          self._thumbnail_click(e, x0, y0, item_width, thumb_size, text_height, pid, path))

                # 强制文字到最顶层，确保不被透明捕获层遮挡
                for tid in (tid1, tid2, tid3, tid4):
                    self.data_canvas.tag_raise(tid)

        if self.total_items > 0:
            self.data_canvas.focus_set()

    def _thumbnail_click(self, event, x0, y0, item_width, thumb_size, text_height, pid, path):
        img_x = x0 + (item_width - thumb_size) // 2
        img_y = y0 + 10
        img_right = img_x + thumb_size
        img_bottom = img_y + thumb_size

        if img_x <= event.x <= img_right and img_y <= event.y <= img_bottom:
            self.open_project_folder(path)
        else:
            self.open_edit_dialog(pid)

    def _bind_hover(self, item, normal_fill, hover_fill):
        self.data_canvas.tag_bind(item, "<Enter>",
            lambda e: self.data_canvas.itemconfig(item, fill=hover_fill))
        self.data_canvas.tag_bind(item, "<Leave>",
            lambda e: self.data_canvas.itemconfig(item, fill=normal_fill))

    def _on_canvas_click(self, event):
        pass
