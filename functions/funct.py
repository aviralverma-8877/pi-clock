import time
from datetime import datetime
import psutil
from gpiozero import CPUTemperature
import socket
import os
import threading
import apt
import apt.progress

CACHE = None
TOTAL_PKG = 0
UPGRADABLE_PKG = 0
UPDATE_IN_PROGRESS = False
UPDATE_PROGRESS = 0
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

        total = 0
        upgradable = 0
        for pkg in list(CACHE):
            total += 1
            if pkg.is_upgradable:
                upgradable += 1

        TOTAL_PKG = total
        UPGRADABLE_PKG = upgradable
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
        # Cache socket connection for IP check
        self._last_ip_check = 0
        self._cached_ip = "Checking..."
        self._cached_ip_status = "Checking..."

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
            return f"T : {TOTAL_PKG}\nU : {UPGRADABLE_PKG}", "In Progress..."
        if comm == "yes":

            def update_thread():
                global TOTAL_PKG, UPGRADABLE_PKG, UPDATE_IN_PROGRESS, CACHE
                total = 0
                upgradable_pkg = 0
                UPDATE_IN_PROGRESS = True
                try:
                    CACHE.update()
                    CACHE.open(None)
                    for pkg in list(CACHE):
                        total += 1
                        if pkg.is_upgradable:
                            upgradable_pkg += 1
                    TOTAL_PKG = total
                    UPGRADABLE_PKG = upgradable_pkg
                except Exception as e:
                    print(f"Error updating cache: {e}")
                finally:
                    UPDATE_IN_PROGRESS = False
                    self.alert()

            x = threading.Thread(target=update_thread)
            x.start()
        elif comm == "no":

            def upgrade_thread():
                global TOTAL_PKG, UPGRADABLE_PKG, UPDATE_IN_PROGRESS, CACHE
                total = 0
                upgradable_pkg = 0
                UPDATE_IN_PROGRESS = True
                try:
                    CACHE.update()
                    CACHE.open(None)
                    CACHE.upgrade(True)
                    CACHE.commit()
                    for pkg in list(CACHE):
                        total += 1
                        if pkg.is_upgradable:
                            upgradable_pkg += 1
                    TOTAL_PKG = total
                    UPGRADABLE_PKG = upgradable_pkg
                except Exception as e:
                    print(f"Error upgrading packages: {e}")
                finally:
                    UPDATE_IN_PROGRESS = False
                    self.alert()

            x = threading.Thread(target=upgrade_thread)
            x.start()
        return f"T : {TOTAL_PKG}\nU : {UPGRADABLE_PKG}", "Upd         Upg"

    def get_disk(self, comm):
        disk = psutil.disk_usage("/")
        free = round(disk.free / (1024 ** 3), 1)
        total = round(disk.total / (1024 ** 3), 1)
        return f"Free {free} GB", f"Total {total} GB"

    def get_time(self, comm):
        if comm in ("yes", "no"):
            self._time_format = comm

        now = datetime.now()
        if self._time_format == "yes":
            return now.strftime("%H:%M:%S"), "24hr      am/pm"
        else:
            return now.strftime("%I:%M:%S %p"), "24hr      am/pm"

    def get_date(self, format):
        now = datetime.now()
        return now.strftime("%d-%m-%Y\n %B"), now.strftime("%A")

    def set_volume(self, comm):
        try:
            if comm == "yes":
                # Increase volume by 5%
                os.system("amixer sset PCM 5%+")
            elif comm == "no":
                # Decrease volume by 5%
                os.system("amixer sset PCM 5%-")
        except Exception as e:
            print(f"Error adjusting volume: {e}")
        return "", "+              -"

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
                self.contrast = self.contrast - 1
                self.disp.contrast = self.contrast
                self.disp.invert = True
        if comm == "no":
            if self.contrast < 70:
                self.contrast = self.contrast + 1
                self.disp.contrast = self.contrast
                self.disp.invert = True
        return "", "+              -"

    def get_cpu(self, comm):
        cpu_freq = psutil.cpu_freq().current
        cpu_pct = psutil.cpu_percent(interval=0)  # Non-blocking
        return f"{cpu_freq:.0f} MHz\n", f"Util {cpu_pct:.1f} %"

    def get_ram(self, comm):
        mem = psutil.virtual_memory()
        fram = round(mem.free / (1024 ** 2), 1)
        uram = round(mem.used / (1024 ** 2), 1)
        rem = round(mem.total / (1024 ** 2), 1)
        return f" F {fram} MB\n U {uram} MB", f"RAM: {rem} MB"

    def get_cpu_temperature(self, comm):
        """get cpu temperature using vcgencmd"""
        cpu = CPUTemperature()
        temp_c = round(cpu.temperature, 2)
        temp_f = round((temp_c * 9 / 5) + 32, 2)
        if comm in ("yes", "no"):
            self._temp_format = comm

        if self._temp_format == "yes":
            return f"{temp_f} F", "F              C"
        else:
            return f"{temp_c} C", "F              C"

    def get_ip(self, comm):
        # Cache IP address for 5 seconds to reduce network checks
        current_time = time.time()
        if current_time - self._last_ip_check > 5.0:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.0)  # Add timeout to prevent hanging
                s.connect(("8.8.8.8", 80))
                self._cached_ip = s.getsockname()[0]
                self._cached_ip_status = "Local IP"
                s.close()
            except:
                self._cached_ip_status = "Link Down"
                self._cached_ip = "Not Available"
            self._last_ip_check = current_time
        return self._cached_ip_status, self._cached_ip

    def no_button_pressed(self):
        if self.next_btn.value:
            if self.prev_btn.value:
                if self.yes_btn.value:
                    if self.no_btn.value:
                        return True
        return False

    def alert(self):
        if self.bkled.value == True:
            self.bkled.value = False
            time.sleep(0.1)
            self.bkled.value = True
            time.sleep(0.1)
            self.bkled.value = False
            time.sleep(0.1)
            self.bkled.value = True
        else:
            self.bkled.value = True
            time.sleep(0.1)
            self.bkled.value = False
            time.sleep(0.1)
            self.bkled.value = True
            time.sleep(0.1)
            self.bkled.value = False
