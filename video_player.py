# ============================================================
# 模块：内嵌视频播放器 (video_player.py) —— 优化进度条拖动
# ============================================================
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk

class VideoPlayer:
    def __init__(self, parent, video_path, width=300, height=200,
                 sync_callback=None, player_id=None):
        self.parent = parent
        self.video_path = video_path
        self.width = width
        self.height = height
        self.sync_callback = sync_callback
        self.player_id = player_id

        self.cap = None
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 30
        self.playing = False
        self.after_id = None
        self.duration = 0.0

        # 进度条拖动优化相关变量
        self._drag_target_frame = None    # 拖动目标帧号
        self._drag_after_id = None        # 延迟跳转的 after id

        self.frame = tk.Frame(parent, bg="#000000")
        self.video_label = tk.Label(self.frame, bg="#000000")
        self.video_label.pack()

        control_frame = tk.Frame(self.frame, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, pady=2)

        self.play_btn = tk.Button(control_frame, text="▶", command=self.toggle_play, width=3)
        self.play_btn.pack(side=tk.LEFT, padx=2)

        self.time_label = tk.Label(control_frame, text="00:00 / 00:00",
                                   bg="#f0f0f0", font=('Microsoft YaHei', 9))
        self.time_label.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(control_frame, from_=0, to=100,
                                      orient=tk.HORIZONTAL,
                                      variable=self.progress_var,
                                      command=self.on_progress_drag)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        tk.Label(control_frame, text="🔇", bg="#f0f0f0",
                 font=('Microsoft YaHei', 9)).pack(side=tk.RIGHT, padx=5)

        self._load_video()

    def _load_video(self):
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                raise Exception("无法打开视频")
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
            self.duration = self.total_frames / self.fps if self.fps > 0 else 0
            self._show_frame(0)
            self._update_time_label()
        except Exception as e:
            self.video_label.config(text=f"视频加载失败: {e}",
                                    bg="#000000", fg="white")

    def _show_frame(self, frame_idx):
        if not self.cap:
            return
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame_idx
                frame = cv2.resize(frame, (self.width, self.height))
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(img)
                self.video_label.config(image=photo)
                self.video_label.image = photo
                if self.total_frames > 0:
                    # 更新进度条（不要触发 command，避免循环）
                    self.progress_var.set((frame_idx / self.total_frames) * 100)
                self._update_time_label()
        except Exception as e:
            print(f"显示帧失败: {e}")

    def _update_time_label(self):
        cur = self.current_frame / self.fps if self.fps > 0 else 0
        tot = self.duration
        self.time_label.config(text=f"{self._format_time(cur)} / {self._format_time(tot)}")

    @staticmethod
    def _format_time(sec):
        m, s = divmod(int(sec), 60)
        return f"{m:02d}:{s:02d}"

    # ---------- 播放控制 ----------
    def toggle_play(self, from_sync=False):
        if not self.cap:
            return
        if self.playing:
            self.playing = False
            self.play_btn.config(text="▶")
            if self.after_id:
                self.parent.after_cancel(self.after_id)
        else:
            self.playing = True
            self.play_btn.config(text="⏸")
            self._play_loop()

        if not from_sync and self.sync_callback and self.player_id is not None:
            self.sync_callback(self.player_id, 'play', self.playing)

    def _play_loop(self):
        if not self.playing or not self.cap:
            return
        nxt = self.current_frame + 1
        if nxt >= self.total_frames:
            nxt = 0
            self.playing = False
            self.play_btn.config(text="▶")
        self._show_frame(nxt)
        if self.playing:
            self.after_id = self.parent.after(int(1000 / self.fps), self._play_loop)

    # ---------- 进度条拖动（优化版） ----------
    def on_progress_drag(self, value):
        """进度条拖动回调，延迟跳转以避免卡顿"""
        if not self.cap or self.total_frames == 0:
            return

        frame_idx = int(float(value) / 100 * self.total_frames)
        self._drag_target_frame = frame_idx

        # 取消之前的延迟跳转
        if self._drag_after_id:
            self.parent.after_cancel(self._drag_after_id)

        # 100ms 后执行跳转，确保拖拽停止后才真正 seek
        self._drag_after_id = self.parent.after(100, self._apply_drag_seek)

    def _apply_drag_seek(self):
        """执行延迟后的跳转"""
        if self._drag_target_frame is None:
            return

        was_playing = self.playing
        if was_playing:
            self.toggle_play()   # 暂停播放

        self._show_frame(self._drag_target_frame)

        if was_playing:
            self.toggle_play()   # 恢复播放

        # 同步到另一个播放器
        if self.sync_callback and self.player_id is not None:
            self.sync_callback(self.player_id, 'seek', self._drag_target_frame)

        self._drag_after_id = None

    # ---------- 外部同步接口 ----------
    def sync_seek(self, frame_idx):
        if not self.cap:
            return
        was_playing = self.playing
        if was_playing:
            self.toggle_play()
        self._show_frame(frame_idx)
        if was_playing:
            self.toggle_play()

    def sync_play_state(self, playing):
        if self.playing != playing:
            self.toggle_play(from_sync=True)

    # ---------- 销毁与布局 ----------
    def destroy(self):
        self.playing = False
        if self.after_id:
            self.parent.after_cancel(self.after_id)
        if self._drag_after_id:
            self.parent.after_cancel(self._drag_after_id)
        if self.cap:
            self.cap.release()
        self.frame.destroy()

    def pack(self, **kw):
        self.frame.pack(**kw)

    def pack_forget(self):
        self.frame.pack_forget()
