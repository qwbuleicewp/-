# ============================================================
# 模块：别名管理 (alias_dialog.py) —— 完整功能版
# ============================================================
import tkinter as tk
from tkinter import ttk, messagebox

class AliasDialogMixin:
    def show_alias_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("别名管理")
        win.geometry("800x500")
        win.configure(bg="#f5f7fa")
        win.bind("<Escape>", lambda e: win.destroy())

        # 三栏主区域
        paned = ttk.PanedWindow(win, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # 左：别名列表
        left = tk.Frame(paned, bg="#f5f7fa")
        paned.add(left, weight=1)
        tk.Label(left, text="别名", bg="#f5f7fa", font=self.bold_font, fg="#000000").pack()
        self.alias_lb = tk.Listbox(left, font=self.base_font, relief="solid", bd=1, fg="#000000")
        self.alias_lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(left, text="删除选中别名", command=self.del_alias, bg="#ffb6c1", fg="#000000",
                  font=self.button_font, padx=8, pady=2, relief="flat").pack(pady=5)

        # 中：标签列表
        mid = tk.Frame(paned, bg="#f5f7fa")
        paned.add(mid, weight=1)
        tk.Label(mid, text="标签", bg="#f5f7fa", font=self.bold_font, fg="#000000").pack()
        self.tag_lb = tk.Listbox(mid, font=self.base_font, relief="solid", bd=1, fg="#000000")
        self.tag_lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(mid, text="删除选中标签", command=self.del_tag, bg="#ffb6c1", fg="#000000",
                  font=self.button_font, padx=8, pady=2, relief="flat").pack(pady=5)

        # 右：预设标签列表
        right = tk.Frame(paned, bg="#f5f7fa")
        paned.add(right, weight=1)
        tk.Label(right, text="预设标签", bg="#f5f7fa", font=self.bold_font, fg="#000000").pack()
        self.preset_lb = tk.Listbox(right, font=self.base_font, relief="solid", bd=1, fg="#000000")
        self.preset_lb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        tk.Button(right, text="删除选中预设", command=self.del_preset, bg="#ffb6c1", fg="#000000",
                  font=self.button_font, padx=8, pady=2, relief="flat").pack(pady=5)

        # 添加别名区域
        add_frame = tk.Frame(win, bg="#f5f7fa")
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(add_frame, text="别名:", bg="#f5f7fa", font=self.bold_font, fg="#000000").grid(row=0, column=0, padx=2)
        alias_ent = tk.Entry(add_frame, font=self.base_font, relief="solid", bd=1, fg="#000000")
        alias_ent.grid(row=0, column=1, padx=2)
        tk.Label(add_frame, text="对应标签:", bg="#f5f7fa", font=self.bold_font, fg="#000000").grid(row=0, column=2, padx=2)
        tag_ent = tk.Entry(add_frame, font=self.base_font, relief="solid", bd=1, fg="#000000")
        tag_ent.grid(row=0, column=3, padx=2)

        def add_alias():
            a = alias_ent.get().strip()
            t = tag_ent.get().strip()
            if not a or not t:
                return
            all_tags = self.all_tags_primary | self.all_tags_secondary | self.preset_tags
            found = next((x for x in all_tags if x.lower() == t.lower()), None)
            if not found:
                messagebox.showerror("错误", f"标签 '{t}' 不存在")
                return
            self.alias_map[a.lower()] = found
            self.refresh_alias_lists()
            alias_ent.delete(0, tk.END)
            tag_ent.delete(0, tk.END)

        alias_ent.bind("<Return>", lambda e: add_alias())
        tag_ent.bind("<Return>", lambda e: add_alias())
        tk.Button(add_frame, text="添加别名", command=add_alias, bg="#ffb6c1", fg="#000000",
                  font=self.button_font, padx=8, pady=2, relief="flat").grid(row=0, column=4, padx=5)

        # 添加预设标签区域
        pre_frame = tk.Frame(win, bg="#f5f7fa")
        pre_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(pre_frame, text="新预设标签:", bg="#f5f7fa", font=self.bold_font, fg="#000000").pack(side=tk.LEFT)
        pre_ent = tk.Entry(pre_frame, font=self.base_font, relief="solid", bd=1, fg="#000000")
        pre_ent.pack(side=tk.LEFT, padx=5)

        def add_preset():
            t = pre_ent.get().strip()
            if t:
                self.preset_tags.add(t)
                self.refresh_alias_lists()
                pre_ent.delete(0, tk.END)

        pre_ent.bind("<Return>", lambda e: add_preset())
        tk.Button(pre_frame, text="添加预设标签", command=add_preset, bg="#ffb6c1", fg="#000000",
                  font=self.button_font, padx=8, pady=2, relief="flat").pack(side=tk.LEFT, padx=5)

        self.refresh_alias_lists()

    def refresh_alias_lists(self):
        self.alias_lb.delete(0, tk.END)
        for a, t in self.alias_map.items():
            self.alias_lb.insert(tk.END, f"{a} -> {t}")
        all_tags = sorted(self.all_tags_primary | self.all_tags_secondary | self.preset_tags)
        self.tag_lb.delete(0, tk.END)
        for t in all_tags:
            self.tag_lb.insert(tk.END, t)
        self.preset_lb.delete(0, tk.END)
        for t in sorted(self.preset_tags):
            self.preset_lb.insert(tk.END, t)

    def del_alias(self):
        sel = self.alias_lb.curselection()
        if sel:
            alias = self.alias_lb.get(sel[0]).split(" -> ")[0].strip()
            key = alias.lower()
            if key in self.alias_map:
                del self.alias_map[key]
                self.refresh_alias_lists()
                self.update_data_and_redraw()

    def del_tag(self):
        sel = self.tag_lb.curselection()
        if sel:
            tag = self.tag_lb.get(sel[0])
            all_projs = self.projects + self.secondary_projects + self.cache_projects + self.cache_secondary
            if any(tag in p.get("tags", []) for p in all_projs):
                messagebox.showwarning("无法删除", f"标签 '{tag}' 正在被使用")
                return
            self.all_tags_primary.discard(tag)
            self.all_tags_secondary.discard(tag)
            self.preset_tags.discard(tag)
            self.refresh_alias_lists()
            self.update_data_and_redraw()

    def del_preset(self):
        sel = self.preset_lb.curselection()
        if sel:
            tag = self.preset_lb.get(sel[0])
            all_projs = self.projects + self.secondary_projects + self.cache_projects + self.cache_secondary
            if any(tag in p.get("tags", []) for p in all_projs):
                messagebox.showwarning("无法删除", f"预设标签 '{tag}' 正在被使用")
                return
            self.preset_tags.discard(tag)
            self.refresh_alias_lists()
            self.update_data_and_redraw()
