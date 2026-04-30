# ============================================================
# 模块：编辑对话框 (edit_dialog.py) —— 完整版
# 功能：项目编辑、保存、删除、添加下一个、保存下一个
# ============================================================
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import config
import utils

class EditDialogMixin:
    def open_edit_dialog(self, pid):
        proj = self._find_project_by_id(pid)
        if not proj:
            return

        # 如果已有编辑窗口，聚焦或关闭旧窗口
        if self.edit_win and self.edit_win.winfo_exists():
            if self.current_edit_id == pid:
                self.flash_window(self.edit_win)
                return
            else:
                self.edit_win.destroy()
                self.edit_win = None
                self.current_edit_id = None

        # 确定项目所在的容器和是否为缓存
        container = None
        for lst in [self.projects, self.secondary_projects, self.cache_projects, self.cache_secondary]:
            if proj in lst:
                container = lst
                break
        is_cache = container in (self.cache_projects, self.cache_secondary)
        target_repo = self.projects if container is self.cache_projects else (
            self.secondary_projects if container is self.cache_secondary else None
        )

        self.current_edit_id = pid
        self.edit_win = tk.Toplevel(self.root)
        self.edit_win.title("编辑项目")
        # 窗口尺寸按屏幕比例
        screen_w = self.edit_win.winfo_screenwidth()
        screen_h = self.edit_win.winfo_screenheight()
        win_w = int(screen_w / 3)
        win_h = int(screen_h * 0.8)
        self.edit_win.geometry(f"{win_w}x{win_h}")
        self.edit_win.configure(bg="#f5f7fa")
        self.edit_win.resizable(True, True)

        edit_font = ('Microsoft YaHei', 13)
        edit_bold = ('Microsoft YaHei', 13, 'bold')
        btn_font = ('Microsoft YaHei', 13, 'bold')

        # 禁止滚轮穿透
        def on_mousewheel(event):
            return "break"
        self.edit_win.bind("<MouseWheel>", on_mousewheel)
        self.edit_win.bind("<Button-4>", on_mousewheel)
        self.edit_win.bind("<Button-5>", on_mousewheel)

        def on_close():
            if self.edit_win:
                self.edit_win.destroy()
            self.edit_win = None
            self.current_edit_id = None
        self.edit_win.protocol("WM_DELETE_WINDOW", on_close)
        self.edit_win.bind("<Escape>", lambda e: on_close())

        # 主布局
        main = tk.Frame(self.edit_win, padx=15, pady=15, bg="#f5f7fa")
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=0)  # 图片列
        main.columnconfigure(1, weight=1)  # 信息列
        main.rowconfigure(0, weight=0)
        main.rowconfigure(1, weight=0)
        main.rowconfigure(2, weight=1)  # 介绍+标签
        main.rowconfigure(3, weight=0)  # 地址
        main.rowconfigure(4, weight=0)  # 按钮

        # ---- 图片预览区 ----
        img_container = tk.Frame(main, bg="#f5f7fa")
        img_container.grid(row=0, column=0, sticky="nw", padx=(0,10), pady=5)

        preview_canvas = tk.Canvas(img_container, width=config.EDIT_PREVIEW_SIZE[0],
                                   height=config.EDIT_PREVIEW_SIZE[1],
                                   bg="#e0e0e0", highlightthickness=1, highlightbackground="#d0d7de")
        preview_canvas.pack(pady=(0,5))

        current_img = proj.get("image")

        def update_preview():
            preview_canvas.delete("all")
            if current_img:
                thumb = utils.base64_to_thumbnail(current_img, config.EDIT_PREVIEW_SIZE)
                if thumb:
                    x = (config.EDIT_PREVIEW_SIZE[0] - thumb.width()) // 2
                    y = (config.EDIT_PREVIEW_SIZE[1] - thumb.height()) // 2
                    preview_canvas.create_image(x, y, image=thumb, anchor=tk.NW)
                    preview_canvas.image = thumb
                    preview_canvas.config(bg="#ffffff")
                else:
                    preview_canvas.create_text(config.EDIT_PREVIEW_SIZE[0]//2,
                                               config.EDIT_PREVIEW_SIZE[1]//2,
                                               text="预览失败", font=edit_font, fill="#666")
            else:
                preview_canvas.create_text(config.EDIT_PREVIEW_SIZE[0]//2,
                                           config.EDIT_PREVIEW_SIZE[1]//2,
                                           text="无图片", font=edit_font, fill="#666")

        def upload_img():
            nonlocal current_img
            addr = proj.get("address", "")
            if addr:
                self.root.clipboard_clear()
                self.root.clipboard_append(addr.strip('"\''))
            path = filedialog.askopenfilename(parent=self.edit_win,
                                              filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif")])
            if path:
                enc = utils.compress_image_to_base64(path, target_size=config.EDIT_PREVIEW_SIZE)
                if enc:
                    current_img = enc
                    update_preview()
                else:
                    messagebox.showerror("错误", "图片压缩失败")

        def clear_img():
            nonlocal current_img
            current_img = None
            update_preview()

        preview_canvas.bind("<Double-Button-1>", lambda e: upload_img())

        btn_img_frame = tk.Frame(img_container, bg="#f5f7fa")
        btn_img_frame.pack()
        tk.Button(btn_img_frame, text="上传图片", command=upload_img, bg="#ffb6c1", fg="#000000",
                  font=btn_font, padx=8, pady=4, relief="flat").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_img_frame, text="清除图片", command=clear_img, bg="#d3d3d3", fg="#000000",
                  font=btn_font, padx=8, pady=4, relief="flat").pack(side=tk.LEFT, padx=2)
        update_preview()

        # ---- 基本信息 ----
        info_frame = tk.Frame(main, bg="#f5f7fa")
        info_frame.grid(row=0, column=1, sticky="nsew", pady=5)
        info_frame.columnconfigure(1, weight=1)

        tk.Label(info_frame, text="名称:", bg="#f5f7fa", font=edit_bold).grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
        name_var = tk.StringVar(value=proj.get("name", ""))
        tk.Entry(info_frame, textvariable=name_var, font=edit_font, relief="solid", bd=1).grid(
            row=0, column=1, sticky="ew", padx=5, pady=6)

        tk.Label(info_frame, text="别名:", bg="#f5f7fa", font=edit_bold).grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
        alias_var = tk.StringVar(value=proj.get("alias", ""))
        tk.Entry(info_frame, textvariable=alias_var, font=edit_font, relief="solid", bd=1).grid(
            row=1, column=1, sticky="ew", padx=5, pady=6)

        tk.Label(info_frame, text="位置:", bg="#f5f7fa", font=edit_bold).grid(row=2, column=0, sticky=tk.W, padx=5, pady=6)
        all_locs = set()
        for lst in [self.projects, self.secondary_projects, self.cache_projects, self.cache_secondary]:
            for p in lst:
                if p.get("location"):
                    all_locs.add(p["location"])
        loc_values = sorted(all_locs)
        loc_var = tk.StringVar(value=proj.get("location", ""))
        loc_combo = ttk.Combobox(info_frame, textvariable=loc_var, values=loc_values,
                                 state="normal", font=edit_font)
        loc_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=6)
        loc_combo.bind("<ButtonPress-1>", lambda e, cb=loc_combo: self._prepare_edit_dropdown(cb))

        # ---- 介绍 ----
        tk.Label(main, text="介绍:", bg="#f5f7fa", font=edit_bold).grid(
            row=1, column=0, sticky=tk.NW, padx=5, pady=(10,2))
        desc_text = tk.Text(main, height=4, font=edit_font, relief="solid", bd=1)
        desc_text.insert(tk.END, proj.get("description", ""))
        desc_text.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0,10))

        # ---- 标签管理 ----
        tk.Label(main, text="标签:", bg="#f5f7fa", font=edit_bold).grid(
            row=3, column=0, sticky=tk.NW, padx=5, pady=(0,2))
        tags_container = tk.Frame(main, bg="#f5f7fa")
        tags_container.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=(0,10))
        tags_container.columnconfigure(0, weight=1)
        tags_container.columnconfigure(1, weight=1)

        # 左侧：添加标签
        left_tag = tk.Frame(tags_container, bg="#f5f7fa")
        left_tag.grid(row=0, column=0, sticky="nsew", padx=(0,5))
        left_tag.columnconfigure(0, weight=1)

        tk.Label(left_tag, text="添加新标签", bg="#f5f7fa", font=edit_bold).grid(row=0, column=0, sticky=tk.W, pady=(0,2))
        input_frm = tk.Frame(left_tag, bg="#f5f7fa")
        input_frm.grid(row=1, column=0, sticky="ew", pady=(0,5))
        input_frm.columnconfigure(0, weight=1)

        all_tags = self.all_tags_primary | self.all_tags_secondary | self.preset_tags
        tag_values = sorted(all_tags)
        tag_var = tk.StringVar()
        tag_combo = ttk.Combobox(input_frm, textvariable=tag_var, values=tag_values,
                                 state="normal", font=edit_font)
        tag_combo.grid(row=0, column=0, sticky="ew", padx=(0,5))
        tag_combo.bind("<ButtonPress-1>", lambda e, cb=tag_combo: self._prepare_edit_dropdown(cb))
        tk.Button(input_frm, text="添加", command=lambda: add_tag_from_input(),
                  bg="#ffb6c1", fg="#000000", font=btn_font, padx=12, pady=2).grid(row=0, column=1)

        # 右侧：已选标签（可滚动）
        right_tag = tk.Frame(tags_container, bg="#f5f7fa")
        right_tag.grid(row=0, column=1, sticky="nsew")
        right_tag.columnconfigure(0, weight=1)
        right_tag.rowconfigure(0, weight=0)
        right_tag.rowconfigure(1, weight=1)

        tk.Label(right_tag, text="已选标签", bg="#f5f7fa", font=edit_bold).grid(row=0, column=0, sticky=tk.W, pady=(0,2))

        canvas = tk.Canvas(right_tag, bg="#f5f7fa", highlightthickness=0)
        scrollbar = tk.Scrollbar(right_tag, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f5f7fa")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        # 滚轮支持
        def _on_canvas_wheel(event):
            if event.delta:
                delta = -int(event.delta / 60)
            elif event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = 0
            canvas.yview_scroll(delta, "units")
            return "break"
        canvas.bind("<MouseWheel>", _on_canvas_wheel)
        canvas.bind("<Button-4>", _on_canvas_wheel)
        canvas.bind("<Button-5>", _on_canvas_wheel)

        tag_rows = []

        def add_tag_row(tag_name):
            row_frm = tk.Frame(scroll_frame, bg="#f5f7fa")
            row_frm.pack(fill=tk.X, pady=1)
            tk.Label(row_frm, text=tag_name, bg="#f5f7fa", font=edit_font, anchor="w").pack(
                side=tk.LEFT, fill=tk.X, expand=True)
            def remove():
                row_frm.destroy()
                tag_rows.remove(row_frm)
            tk.Button(row_frm, text="✕", command=remove, bg="#e74c3c", fg="white",
                      font=('Microsoft YaHei', 9, 'bold'), relief="flat", padx=4).pack(side=tk.RIGHT)
            tag_rows.append(row_frm)

        for t in proj.get("tags", []):
            if t:
                add_tag_row(t)

        def add_tag_from_input():
            new_tag = tag_var.get().strip()
            if not new_tag:
                return
            for row in tag_rows:
                lbl = row.winfo_children()[0]
                if lbl.cget("text") == new_tag:
                    tag_var.set("")
                    return
            add_tag_row(new_tag)
            if new_tag not in tag_values:
                tag_values.append(new_tag)
                tag_values.sort()
                tag_combo['values'] = tag_values
            tag_var.set("")

        tag_combo.bind("<Return>", lambda e: add_tag_from_input())
        tag_combo.bind("<<ComboboxSelected>>", lambda e: (tag_var.set(tag_combo.get()), add_tag_from_input()))

        # ---- 地址 ----
        addr_frame = tk.Frame(main, bg="#f5f7fa")
        addr_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=(0,5))
        addr_frame.columnconfigure(1, weight=1)
        tk.Label(addr_frame, text="地址:", bg="#f5f7fa", font=edit_bold).grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        addr_var = tk.StringVar(value=proj.get("address", ""))
        tk.Entry(addr_frame, textvariable=addr_var, font=edit_font, relief="solid", bd=1).grid(
            row=0, column=1, sticky="ew")

        # ---- 工具函数 ----
        def get_tags():
            tags = []
            for row in tag_rows:
                lbl = row.winfo_children()[0]
                tags.append(lbl.cget("text"))
            return tags

        def save_changes():
            proj["name"] = name_var.get()
            proj["alias"] = alias_var.get()
            proj["description"] = desc_text.get("1.0", tk.END).strip()
            proj["location"] = loc_var.get().strip()
            proj["address"] = addr_var.get()
            proj["tags"] = get_tags()
            proj["image"] = current_img

            if container in (self.projects, self.cache_projects):
                tag_set = self.all_tags_primary
            else:
                tag_set = self.all_tags_secondary
            for t in proj["tags"]:
                tag_set.add(t)

            if pid in self.thumbnail_cache:
                del self.thumbnail_cache[pid]
            self.update_data_and_redraw()

        # ---- 按钮命令 ----
        def save_and_close():
            save_changes()
            on_close()

        def delete_and_close():
            if messagebox.askyesno("确认删除", "确定删除此项目吗？"):
                # 从所有列表中移除
                for lst in [self.projects, self.secondary_projects, self.cache_projects, self.cache_secondary]:
                    if proj in lst:
                        lst.remove(proj)
                        break
                if pid in self.thumbnail_cache:
                    del self.thumbnail_cache[pid]
                self.update_data_and_redraw()
                on_close()

        def get_next_proj():
            """获取当前视图下 filtered_list 中的下一个项目"""
            filtered = self.get_filtered_list()
            idx = next((i for i, p in enumerate(filtered) if p["id"] == pid), None)
            if idx is not None and idx + 1 < len(filtered):
                return filtered[idx + 1]
            return None

        def add_next():
            """添加：保存并移到仓库，然后打开下一个"""
            if not is_cache or target_repo is None:
                messagebox.showinfo("提示", "只有缓存项目可以添加到仓库")
                return
            save_changes()
            # 从缓存移除并添加到仓库
            container.remove(proj)
            target_repo.append(proj)
            self.update_data_and_redraw()
            on_close()
            nxt = get_next_proj()
            if nxt:
                self.root.after(50, lambda: self.open_edit_dialog(nxt["id"]))
            else:
                messagebox.showinfo("完成", "已处理最后一个项目")

        def save_next():
            """保存但不移动，打开下一个"""
            save_changes()
            on_close()
            nxt = get_next_proj()
            if nxt:
                self.root.after(50, lambda: self.open_edit_dialog(nxt["id"]))
            else:
                messagebox.showinfo("完成", "已保存最后一个项目")

        # ---- 底部按钮 ----
        btn_row = tk.Frame(main, bg="#f5f7fa")
        btn_row.grid(row=6, column=0, columnspan=2, pady=20)

        # 保存 (浅绿底)
        tk.Button(btn_row, text="保存", command=save_and_close,
                  bg="#e8f5e9", fg="#000000", font=btn_font, padx=16, pady=6, relief="flat").pack(
            side=tk.LEFT, padx=5)
        # 删除 (浅红底)
        tk.Button(btn_row, text="删除", command=delete_and_close,
                  bg="#ffebee", fg="#000000", font=btn_font, padx=16, pady=6, relief="flat").pack(
            side=tk.LEFT, padx=5)
        # 缓存专属按钮
        if is_cache:
            tk.Button(btn_row, text="添加下一个", command=add_next,
                      bg="#d3d3d3", fg="#000000", font=btn_font, padx=16, pady=6, relief="flat").pack(
                side=tk.LEFT, padx=5)
            tk.Button(btn_row, text="保存下一个", command=save_next,
                      bg="#d3d3d3", fg="#000000", font=btn_font, padx=16, pady=6, relief="flat").pack(
                side=tk.LEFT, padx=5)

    def _prepare_edit_dropdown(self, cb):
        cb.after(10, lambda: cb.event_generate('<Down>'))

    def flash_window(self, win):
        win.lift()
        win.focus_force()
        win.bell()
