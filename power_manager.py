# ============================================================
# 模块：功耗管理 (power_manager.py)
# ============================================================
import platform
import psutil
import config

class PowerManager:
    def __init__(self, mode=config.POWER_MODE_NORMAL):
        self.mode = mode
        self.process = psutil.Process()
        self._apply_mode()

    def set_mode(self, mode):
        if mode == self.mode:
            return
        self.mode = mode
        self._apply_mode()

    def _apply_mode(self):
        try:
            if self.mode == config.POWER_MODE_LOW:
                if platform.system() == 'Windows':
                    self.process.nice(psutil.IDLE_PRIORITY_CLASS)
                else:
                    self.process.nice(19)
                cpu_count = psutil.cpu_count(logical=True)
                if cpu_count and cpu_count > 4:
                    low_cores = list(range(cpu_count // 2, cpu_count))
                    self.process.cpu_affinity(low_cores)
            else:
                if platform.system() == 'Windows':
                    self.process.nice(psutil.NORMAL_PRIORITY_CLASS)
                else:
                    self.process.nice(0)
                cpu_count = psutil.cpu_count(logical=True)
                if cpu_count:
                    self.process.cpu_affinity(list(range(cpu_count)))
        except Exception as e:
            print(f"功耗模式设置失败: {e}")
