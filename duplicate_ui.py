# ============================================================
# 模块：查重页面 UI 构建 (duplicate_ui.py) —— 美化版
# ============================================================
import tkinter as tk
from tkinter import ttk

class DuplicateUIMixin:
    def build_duplicate_ui(self):
        for w in self.duplicate_frame.winfo_children():
            w.destroy()

        dup_font = ('Microsoft YaHei', 15)
        dup_bold = ('Microsoft YaHei', 15, 'bold')

        # ===== 顶部控制栏 =====
        ctrl_top = tk.Frame(self.duplicate_frame, bg="#f0f3f8")
        ctrl_top.pack(fill=tk.X, padx=10, pady=(5, 0))
        ctrl_bottom = tk.Frame(self.duplicate_frame, bg="#f0f3f8")
        ctrl_bottom.pack(fill=tk.X, padx=10, pady=(0, 5))

        tk.Label(ctrl_top, text="查重条件:", bg="#f0f3f8", font=dup_bold).pack(side=tk.LEFT, padx=5)

        # 条件变量
        self.dup_var_hash = tk.BooleanVar(value=True)
        self.dup_var_size = tk.BooleanVar(value=False)
        self.dup_var_name = tk.BooleanVar(value=False)
        self.dup_var_image = tk.BooleanVar(value=False)
        self.dup_var_video = tk.BooleanVar(value=False)
        self.dup_var_archive = tk.BooleanVar(value=False)
        self.dup_var_mtime = tk.BooleanVar(value=False)
        self.video_method = tk.StringVar(value="fast")

        for text, var in [("内容相同", self.dup_var_hash), ("大小相同", self.dup_var_size),
                          ("文件名相似", self.dup_var_name), ("相似图片", self.dup_var_image)]:
            tk.Checkbutton(ctrl_top, text=text, variable=var, bg="#f0f3f8",
                           font=dup_font).pack(side=tk.LEFT, padx=2)

        tk.Label(ctrl_top, text="名称阈值:", bg="#f0f3f8", font=dup_font).pack(side=tk.LEFT, padx=(10, 2))
        self.dup_name_th = ttk.Entry(ctrl_top, width=5, font=dup_font)
        self.dup_name_th.insert(0, "0.8")
        self.dup_name_th.pack(side=tk.LEFT)

        tk.Label(ctrl_top, text="图片汉明:", bg="#f0f3f8", font=dup_font).pack(side=tk.LEFT, padx=(10, 2))
        self.dup_img_th = ttk.Entry(ctrl_top, width=5, font=dup_font)
        self.dup_img_th.insert(0, "10")
        self.dup_img_th.pack(side=tk.LEFT)

        tk.Label(ctrl_top, text="时间差(秒):", bg="#f0f3f8", font=dup_font).pack(side=tk.LEFT, padx=(10, 2))
        self.dup_time_th = ttk.Entry(ctrl_top, width=6, font=dup_font)
        self.dup_time_th.insert(0, "60")
        self.dup_time_th.pack(side=tk.LEFT)

        for text, var in [("相似视频", self.dup_var_video), ("相似压缩包", self.dup_var_archive),
                          ("修改时间相近", self.dup_var_mtime)]:
            tk.Checkbutton(ctrl_bottom, text=text, variable=var, bg="#f0f3f8",
                           font=dup_font).pack(side=tk.LEFT, padx=2)

        tk.Label(ctrl_bottom, text="视频阈值:", bg="#f0f3f8", font=dup_font).pack(side=tk.LEFT, padx=(10, 2))
        self.dup_video_th = ttk.Entry(ctrl_bottom, width=5, font=dup_font)
        self.dup_video_th.insert(0, "15")
        self.dup_video_th.pack(side=tk.LEFT)

        tk.Label(ctrl_bottom, text="视频方案:", bg="#f0f3f8", font=dup_font).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Radiobutton(ctrl_bottom, text="快速", variable=self.video_method, value="fast").pack(side=tk.LEFT)
        ttk.Radiobutton(ctrl_bottom, text="精准", variable=self.video_method, value="accurate").pack(side=tk.LEFT)

        tk.Label(ctrl_bottom, text="压缩包阈值:", bg="#f0f3f8", font=dup_font).pack(side=tk.LEFT, padx=(10, 2))
        self.dup_archive_th = ttk.Entry(ctrl_bottom, width=5, font=dup_font)
        self.dup_archive_th.insert(0, "0.9")
        self.dup_archive_th.pack(side=tk.LEFT)

        ttk.Button(ctrl_bottom, text="🔍 开始查重", command=self.start_duplicate_detection,
                   style="Large.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(ctrl_bottom, text="📂 加载数据", command=self.load_scan_data_for_duplicate,
                   style="Large.TButton").pack(side=tk.LEFT, padx=5)

        self.dup_status = tk.Label(ctrl_bottom, text="未扫描", bg="#f0f3f8", fg="#666", font=dup_font)
        self.dup_status.pack(side=tk.RIGHT, padx=10)

        # ===== 主分栏 =====
        paned = ttk.PanedWindow(self.duplicate_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ===== 左侧：树形列表 =====
        left = tk.Frame(paned, bg="#ffffff")
        paned.add(left, weight=2)

        header_frame = tk.Frame(left, bg="#f0f3f8")
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="名字", bg="#f0f3f8", font=dup_bold,
                 width=30, anchor=tk.W).pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="类型", bg="#f0f3f8", font=dup_bold,
                 width=8, anchor=tk.W).pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="路径", bg="#f0f3f8", font=dup_bold,
                 anchor=tk.W).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        tree_frame = tk.Frame(left, bg="#ffffff")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.dup_tree = ttk.Treeview(tree_frame, columns=("type", "path"),
                                     show="tree", selectmode="extended")
        self.dup_tree.heading("#0", text="")
        self.dup_tree.column("#0", width=350, stretch=True)
        self.dup_tree.column("type", width=80, stretch=False)
        self.dup_tree.column("path", width=300, stretch=True)

        tree_style = ttk.Style()
        tree_style.configure("Treeview", font=dup_font, rowheight=32,
                           background="#ffffff", fieldbackground="#ffffff",
                           foreground="#000000", borderwidth=1, relief="solid")
        tree_style.configure("Treeview.Heading", font=dup_bold, relief="flat")
        tree_style.map("Treeview", background=[('selected', '#d3d3d3')])

        ysb = tk.Scrollbar(tree_frame, orient="vertical", command=self.dup_tree.yview)
        xsb = tk.Scrollbar(tree_frame, orient="horizontal", command=self.dup_tree.xview)
        self.dup_tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

        self.dup_tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.dup_tree.bind("<ButtonRelease-1>", self.on_tree_click)
        self.dup_tree.bind("<Double-Button-1>", self.on_tree_double)
        self.dup_tree.bind("<Button-3>", self.on_tree_right_click)

        btn_row = tk.Frame(left, bg="#ffffff")
        btn_row.pack(fill=tk.X, pady=5)
        tk.Button(btn_row, text="保留一份", command=self.dup_keep_one,
                  bg="#ffb6c1", fg="#000000", font=dup_font, padx=12, pady=4, relief="flat").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text="删除选中", command=self.dup_delete_selected,
                  bg="#e74c3c", fg="white", font=dup_font, padx=12, pady=4, relief="flat").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_row, text="取消选择", command=self.dup_cancel_selection,
                  bg="#d3d3d3", fg="#000000", font=dup_font, padx=12, pady=4, relief="flat").pack(side=tk.LEFT, padx=5)

        # ===== 右侧预览区 =====
        right = tk.Frame(paned, bg="#fafafa")
        paned.add(right, weight=1)

        self.preview_frame_a = tk.Frame(right, bg="#fafafa")
        self.preview_frame_a.pack(fill=tk.BOTH, expand=True)
        self.preview_title_a = tk.Label(self.preview_frame_a, text="预览 A",
                                        bg="#fafafa", font=dup_bold, anchor=tk.W)
        self.preview_title_a.pack(fill=tk.X, padx=5, pady=2)
        self.preview_label_a = tk.Label(self.preview_frame_a, bg="#fafafa")
        self.preview_info_a = tk.Text(self.preview_frame_a, height=6, state='normal',
                                     bg="#fafafa", relief="flat", font=dup_font, wrap=tk.WORD)

        tk.Frame(right, height=2, bg="#cccccc").pack(fill=tk.X, padx=10, pady=5)

        self.preview_frame_b = tk.Frame(right, bg="#fafafa")
        self.preview_frame_b.pack(fill=tk.BOTH, expand=True)
        self.preview_title_b = tk.Label(self.preview_frame_b, text="预览 B",
                                        bg="#fafafa", font=dup_bold, anchor=tk.W)
        self.preview_title_b.pack(fill=tk.X, padx=5, pady=2)
        self.preview_label_b = tk.Label(self.preview_frame_b, bg="#fafafa")
        self.preview_info_b = tk.Text(self.preview_frame_b, height=6, state='normal',
                                     bg="#fafafa", relief="flat", font=dup_font, wrap=tk.WORD)

        self.preview_titles = [self.preview_title_a, self.preview_title_b]
        self.preview_labels = [self.preview_label_a, self.preview_label_b]
        self.preview_infos = [self.preview_info_a, self.preview_info_b]
        self.video_players = [None, None]
        self.archive_internal_state = [None, None]
