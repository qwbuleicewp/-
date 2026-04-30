# ============================================================
# 模块：系统托盘 (tray.py) —— 完整版
# ============================================================
import threading
import tkinter as tk
import pystray
from PIL import Image as PILImage, ImageDraw
import config

class TrayMixin:
    def create_tray_image(self):
        img = PILImage.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((12, 28, 52, 52), fill='#8B4513', outline='#5D2E0C', width=2)
        draw.polygon([(12, 28), (4, 16), (24, 20), (32, 28)], fill='#A0522D', outline='#5D2E0C', width=2)
        draw.polygon([(52, 28), (60, 16), (40, 20), (32, 28)], fill='#A0522D', outline='#5D2E0C', width=2)
        draw.rectangle((14, 20, 50, 28), fill='#F5F5DC')
        draw.rectangle((24, 36, 40, 48), fill='#F5DEB3', outline='#5D2E0C', width=1)
        draw.text((28, 38), "📦", fill='black')
        return img

    def create_tray_image_with_glass(self):
        img = self.create_tray_image()
        draw = ImageDraw.Draw(img)
        draw.ellipse((44, 4, 60, 20), outline='#333333', width=3, fill='#88CCFF')
        draw.line((56, 16, 62, 24), fill='#333333', width=4)
        return img

    def update_tray_icon(self, scanning=False):
        if not self.tray_icon:
            return
        self.tray_icon.icon = self.create_tray_image_with_glass() if scanning else self.create_tray_image()

    def _tray_switch_view(self, view_name):
        self.show_from_tray()
        self.root.after(100, lambda: self.switch_view(view_name))

    def setup_tray(self):
        image = self.create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self.show_from_tray, default=True),
            pystray.MenuItem("主仓库", lambda: self._tray_switch_view("warehouse")),
            pystray.MenuItem("副仓库", lambda: self._tray_switch_view("secondary")),
            pystray.MenuItem("查重页面", lambda: self._tray_switch_view("duplicate")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("视图模式: 详细", self._toggle_tray_view_mode,
                             checked=lambda item: self.warehouse_view_mode == config.VIEW_MODE_TABLE),
            pystray.MenuItem("视图模式: 缩略图", self._toggle_tray_view_mode,
                             checked=lambda item: self.warehouse_view_mode == config.VIEW_MODE_THUMBNAIL),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("低功耗模式", self.toggle_low_power_mode,
                             checked=lambda item: self.power_mode == config.POWER_MODE_LOW),
            pystray.MenuItem("正常模式", self.toggle_normal_mode,
                             checked=lambda item: self.power_mode == config.POWER_MODE_NORMAL),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("查看扫描进度", self.show_scan_progress_from_tray,
                             enabled=lambda item: self.scan_thread is not None and self.scan_thread.is_alive()),
            pystray.MenuItem("退出", self.quit_app)
        )
        self.tray_icon = pystray.Icon("warehouse_tool", image, "仓库管理工具", menu)
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def _toggle_tray_view_mode(self, icon, item):
        if self.warehouse_view_mode == config.VIEW_MODE_TABLE:
            self.warehouse_view_mode = config.VIEW_MODE_THUMBNAIL
        else:
            self.warehouse_view_mode = config.VIEW_MODE_TABLE
        if hasattr(self, 'view_mode_btn'):
            if self.warehouse_view_mode == config.VIEW_MODE_TABLE:
                self.view_mode_btn.config(text="📋 列表模式")
            else:
                self.view_mode_btn.config(text="🖼️ 缩略图模式")
        self.update_data_and_redraw()

    def show_scan_progress_from_tray(self):
        if self.scan_progress_win and self.scan_progress_win.winfo_exists():
            self.scan_progress_win.lift()
            self.scan_progress_win.focus_force()
        else:
            self.create_scan_progress_window()

    def hide_to_tray(self):
        if self.tray_icon:
            self.root.withdraw()
        else:
            self.quit_app()

    def show_from_tray(self, icon=None, item=None):
        self.root.after(0, self._show_window)

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def toggle_low_power_mode(self, icon=None, item=None):
        self.power_mode = config.POWER_MODE_LOW
        self.power_manager.set_mode(config.POWER_MODE_LOW)
        self.save_config()
        if icon:
            icon.update_menu()

    def toggle_normal_mode(self, icon=None, item=None):
        self.power_mode = config.POWER_MODE_NORMAL
        self.power_manager.set_mode(config.POWER_MODE_NORMAL)
        self.save_config()
        if icon:
            icon.update_menu()

    def quit_app(self, icon=None, item=None):
        if self.unified_scanner:
            self.unified_scanner.stop()
        if self.dup_engine:
            self.dup_engine.stop()
        self.save_all()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        import sys
        sys.exit(0)
