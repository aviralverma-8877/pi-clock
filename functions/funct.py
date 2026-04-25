import time
from datetime import datetime
import psutil
from gpiozero import CPUTemperature
import socket
import os
import subprocess
import threading
import apt
import apt.progress

CACHE = None
TOTAL_PKG = 0
UPGRADABLE_PKG = 0
UPDATE_IN_PROGRESS = False
CACHE_INITIALIZED = False
CACHE_INITIALIZING = False


def initialize_cache():
    global CACHE, TOTAL_PKG, UPGRADABLE_PKG, CACHE_INITIALIZED, CACHE_INITIALIZING
    if CACHE_INITIALIZED or CACHE_INITIALIZING:
        return CACHE_INITIALIZED
    CACHE_INITIALIZING = True
    try:
        CACHE = apt.Cache()
        CACHE.open(None)
        TOTAL_PKG = sum(1 for _ in CACHE)
        UPGRADABLE_PKG = sum(1 for pkg in CACHE if pkg.is_upgradable)
        CACHE_INITIALIZED = True
        return True
    except Exception as e:
        print(f"Error initializing APT cache: {e}")
        return False
    finally:
        CACHE_INITIALIZING = False


class function(object):
    def __init__(self, prev_btn, next_btn, yes_btn, no_btn, bkled, disp, contrast):
        self.prev_btn = prev_btn
        self.next_btn = next_btn
        self.yes_btn = yes_btn
        self.no_btn = no_btn
        self.bkled = bkled
        self.disp = disp
        self.contrast = contrast
        self.last_comm = "no"
        self._time_format = "no"
        self._temp_format = "no"
        # IP cache
        self._last_ip_check = 0
        self._cached_ip = "Checking..."
        self._cached_ip_status = "Checking..."
        # Sensor caches
        self._cpu_freq = 0.0
        self._cpu_pct = 0.0
        self._last_cpu_time = 0.0
        self._ram_free = 0.0
        self._ram_used = 0.0
        self._ram_total = 0.0
        self._last_ram_time = 0.0
        self._disk_free = 0.0
        self._disk_total = 0.0
        self._last_disk_time = 0.0
        self._temp_c = 0.0
        self._last_temp_time = 0.0

    def _refresh_cpu(self):
        now = time.time()
        if now - self._last_cpu_time >= 1.0:
            try:
                self._cpu_freq = psutil.cpu_freq().current
                self._cpu_pct = psutil.cpu_percent(interval=0)
            except Exception:
                pass
            self._last_cpu_time = now

    def _refresh_ram(self):
        now = time.time()
        if now - self._last_ram_time >= 1.0:
            try:
                mem = psutil.virtual_memory()
                self._ram_free = round(mem.free / (1024 ** 2), 0)
                self._ram_used = round(mem.used / (1024 ** 2), 0)
                self._ram_total = round(mem.total / (1024 ** 2), 0)
            except Exception:
                pass
            self._last_ram_time = now

    def _refresh_disk(self):
        now = time.time()
        if now - self._last_disk_time >= 10.0:
            try:
                disk = psutil.disk_usage("/")
                self._disk_free = round(disk.free / (1024 ** 3), 1)
                self._disk_total = round(disk.total / (1024 ** 3), 1)
            except Exception:
                pass
            self._last_disk_time = now

    def _refresh_temp(self):
        now = time.time()
        if now - self._last_temp_time >= 1.0:
            try:
                self._temp_c = round(CPUTemperature().temperature, 1)
            except Exception:
                pass
            self._last_temp_time = now

    def toggleBkled(self, comm):
        if comm == "no":
            self.bkled.value = True
            return "  ON", "OFF           ON"
        elif comm == "yes":
            self.bkled.value = False
            return "  OFF", "OFF           ON"
        else:
            if self.bkled.value:
                return "  ON", "OFF           ON"
            else:
                return "  OFF", "OFF           ON"

    def sys_upgrade(self, comm):
        global UPDATE_IN_PROGRESS, CACHE_INITIALIZED, CACHE_INITIALIZING

        if not CACHE_INITIALIZED:
            if not CACHE_INITIALIZING:
                threading.Thread(target=initialize_cache, daemon=True).start()
            return "Loading...", "Please wait"

        if UPDATE_IN_PROGRESS:
            return f"T:{TOTAL_PKG} U:{UPGRADABLE_PKG}", "In Progress..."

        if comm == "yes":
            def update_thread():
                global TOTAL_PKG, UPGRADABLE_PKG, UPDATE_IN_PROGRESS, CACHE
                UPDATE_IN_PROGRESS = True
                try:
                    CACHE.update()
                    CACHE.open(None)
                    TOTAL_PKG = sum(1 for _ in CACHE)
                    UPGRADABLE_PKG = sum(1 for pkg in CACHE if pkg.is_upgradable)
                except Exception as e:
                    print(f"Error updating cache: {e}")
                finally:
                    UPDATE_IN_PROGRESS = False
                    self.alert()
            threading.Thread(target=update_thread, daemon=True).start()

        elif comm == "no":
            def upgrade_thread():
                global TOTAL_PKG, UPGRADABLE_PKG, UPDATE_IN_PROGRESS, CACHE
                UPDATE_IN_PROGRESS = True
                try:
                    CACHE.update()
                    CACHE.open(None)
                    CACHE.upgrade(True)
                    CACHE.commit()
                    TOTAL_PKG = sum(1 for _ in CACHE)
                    UPGRADABLE_PKG = sum(1 for pkg in CACHE if pkg.is_upgradable)
                except Exception as e:
                    print(f"Error upgrading packages: {e}")
                finally:
                    UPDATE_IN_PROGRESS = False
                    self.alert()
            threading.Thread(target=upgrade_thread, daemon=True).start()

        return f"T:{TOTAL_PKG} U:{UPGRADABLE_PKG}", "Upd         Upg"

    def get_disk(self, comm):
        self._refresh_disk()
        return f"Free {self._disk_free}GB", f"Tot {self._disk_total}GB"

    def get_time(self, comm):
        if comm in ("yes", "no"):
            self._time_format = comm
        now = datetime.now()
        if self._time_format == "yes":
            return now.strftime("%H:%M:%S"), "24hr      am/pm"
        else:
            return now.strftime("%I:%M %p"), "24hr      am/pm"

    def get_date(self, comm):
        now = datetime.now()
        return now.strftime("%d %b %Y"), now.strftime("%A")

    def set_volume(self, comm):
        vol_str = ""
        try:
            if comm == "yes":
                subprocess.run(["amixer", "sset", "PCM", "5%+"],
                               capture_output=True, timeout=1)
            elif comm == "no":
                subprocess.run(["amixer", "sset", "PCM", "5%-"],
                               capture_output=True, timeout=1)
            result = subprocess.run(
                ["amixer", "sget", "PCM"],
                capture_output=True, text=True, timeout=1
            )
            for line in result.stdout.splitlines():
                if "%" in line:
                    start = line.find("[") + 1
                    end = line.find("%")
                    if 0 < start <= end:
                        vol_str = f"{line[start:end]}%"
                        break
        except Exception as e:
            print(f"Error adjusting volume: {e}")
        return vol_str, "+              -"

    def shutdown(self, comm):
        if comm == "yes" and self.last_comm != "shutdown":
            self.last_comm = "shutdown"
            def do_shutdown():
                time.sleep(0.5)
                os.system("shutdown -h now")
            threading.Thread(target=do_shutdown, daemon=True).start()
        if self.last_comm == "shutdown":
            return "", "yes         Wait.."
        return "", "yes           no"

    def restart(self, comm):
        if comm == "yes" and self.last_comm != "rebooting":
            self.last_comm = "rebooting"
            def do_reboot():
                time.sleep(0.5)
                os.system("reboot")
            threading.Thread(target=do_reboot, daemon=True).start()
        if self.last_comm == "rebooting":
            return "", "yes         Wait.."
        return "", "yes           no"

    def set_contrast(self, comm):
        if comm == "yes":
            if self.contrast > 40:
                self.contrast -= 1
                self.disp.contrast = self.contrast
                self.disp.invert = True
        elif comm == "no":
            if self.contrast < 70:
                self.contrast += 1
                self.disp.contrast = self.contrast
                self.disp.invert = True
        return "", "+              -"

    def get_cpu(self, comm):
        self._refresh_cpu()
        return f"{self._cpu_freq:.0f}MHz", f"Util {self._cpu_pct:.1f}%"

    def get_ram(self, comm):
        self._refresh_ram()
        return f"F:{self._ram_free:.0f}MB", f"U:{self._ram_used:.0f} T:{self._ram_total:.0f}"

    def get_cpu_temperature(self, comm):
        if comm in ("yes", "no"):
            self._temp_format = comm
        self._refresh_temp()
        if self._temp_format == "yes":
            temp_f = round((self._temp_c * 9 / 5) + 32, 1)
            return f"{temp_f}F", "F              C"
        else:
            return f"{self._temp_c}C", "F              C"

    def get_ip(self, comm):
        now = time.time()
        if now - self._last_ip_check > 5.0:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.0)
                s.connect(("8.8.8.8", 80))
                self._cached_ip = s.getsockname()[0]
                self._cached_ip_status = "Local IP"
                s.close()
            except Exception:
                self._cached_ip_status = "Link Down"
                self._cached_ip = "Not Available"
            self._last_ip_check = now
        return self._cached_ip_status, self._cached_ip

    def no_button_pressed(self):
        return (self.next_btn.value and self.prev_btn.value and
                self.yes_btn.value and self.no_btn.value)

    def alert(self):
        original = self.bkled.value
        for _ in range(2):
            self.bkled.value = not original
            time.sleep(0.1)
            self.bkled.value = original
            time.sleep(0.1)
