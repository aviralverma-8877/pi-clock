import time
from datetime import datetime
import psutil
from gpiozero import CPUTemperature
import socket
import os
import subprocess
import threading
import json
import re
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
        # Voice assistant state
        self._asst_state = 'init'   # init|idle|listening|processing|showing
        self._asst_loading = False
        self._asst_whisper_model = None
        self._asst_mic_idx = None
        self._asst_transcript = ''
        self._asst_lines = []
        self._asst_scroll = 0
        self._asst_start_time = 0.0

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

    # ── Voice assistant ────────────────────────────────────────────────────────

    def _asst_load_whisper(self):
        try:
            from faster_whisper import WhisperModel
            model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     '..', 'models')
            self._asst_whisper_model = WhisperModel(
                'tiny.en', device='cpu', compute_type='int8',
                download_root=model_dir,
            )
            self._asst_state = 'idle'
        except Exception as e:
            print(f"Whisper load error: {e}")
            self._asst_lines = self._asst_wrap(f"Whisper error: {e}")
            self._asst_state = 'showing'

    def _asst_find_mic(self):
        try:
            import sounddevice as sd
            for i, d in enumerate(sd.query_devices()):
                if d['max_input_channels'] > 0 and 'USB' in str(d.get('name', '')):
                    return i
            for i, d in enumerate(sd.query_devices()):
                if d['max_input_channels'] > 0:
                    return i
        except Exception as e:
            print(f"Mic find error: {e}")
        return None

    def _asst_record_and_process(self):
        import sounddevice as sd
        import numpy as np

        RATE     = 16000
        DURATION = 6

        try:
            if self._asst_mic_idx is None:
                self._asst_mic_idx = self._asst_find_mic()
            if self._asst_mic_idx is None:
                self._asst_lines = ["No mic found"]
                self._asst_state = 'showing'
                return

            # Prefer recording at 16 kHz directly; fall back to native rate + resample
            try:
                audio = sd.rec(int(DURATION * RATE), samplerate=RATE, channels=1,
                               dtype='float32', device=self._asst_mic_idx)
                sd.wait()
                audio = audio.flatten()
            except Exception:
                dev_info    = sd.query_devices(self._asst_mic_idx)
                native_rate = int(dev_info['default_samplerate'])
                audio = sd.rec(int(DURATION * native_rate), samplerate=native_rate,
                               channels=1, dtype='float32', device=self._asst_mic_idx)
                sd.wait()
                audio = audio.flatten()
                try:
                    from scipy.signal import resample_poly
                    from math import gcd
                    g = gcd(RATE, native_rate)
                    audio = resample_poly(audio, RATE // g, native_rate // g).astype(np.float32)
                except ImportError:
                    n_out = int(len(audio) * RATE / native_rate)
                    audio = np.interp(
                        np.linspace(0, len(audio) - 1, n_out),
                        np.arange(len(audio)), audio,
                    ).astype(np.float32)

            self._asst_state = 'processing'

            segments, _ = self._asst_whisper_model.transcribe(
                audio, beam_size=5, language='en',
            )
            self._asst_transcript = ' '.join(seg.text for seg in segments).strip()
            print(f"Heard: {self._asst_transcript!r}")

            if not self._asst_transcript:
                self._asst_lines = ["Could not hear.", "Press YES to retry", "NO=back"]
                self._asst_state = 'showing'
                return

            self._asst_answer(self._asst_transcript)

        except Exception as e:
            print(f"Record error: {e}")
            self._asst_lines = self._asst_wrap(f"Error: {e}")
            self._asst_state = 'showing'

    def _asst_answer(self, text):
        q = text.lower()

        m = re.search(r'weather (?:in |at |for )?(.+?)(?:\?|$)', q)
        if m:
            city = m.group(1).strip()
            ans = self._asst_sanitise(self._asst_weather(city))
            self._asst_lines = self._asst_wrap(f"Weather {city}: {ans}")
            self._asst_state = 'showing'
            return

        m = re.search(r'(?:price of |stock (?:price )?(?:of |for )?|how much (?:is |does )?)([a-z][a-z\s]+?)(?:\?|$)', q)
        if m:
            raw = m.group(1).strip()
            ans = self._asst_sanitise(self._asst_stock(raw))
            self._asst_lines = self._asst_wrap(f"{raw.upper()}: {ans}")
            self._asst_state = 'showing'
            return

        m = re.search(r'air quality (?:in |at |for )?(.+?)(?:\?|$)', q)
        if m:
            city = m.group(1).strip()
            ans = self._asst_sanitise(self._asst_air_quality(city))
            self._asst_lines = self._asst_wrap(f"AQI {city}: {ans}")
            self._asst_state = 'showing'
            return

        ans = self._asst_sanitise(self._asst_ollama(text))
        self._asst_lines = self._asst_wrap(ans)
        self._asst_state = 'showing'

    def _asst_weather(self, city):
        import requests
        try:
            r = requests.get(f'https://wttr.in/{city}?format=j1', timeout=5)
            data = r.json()
            cc   = data['current_condition'][0]
            desc = cc['weatherDesc'][0]['value']
            tc   = cc['temp_C']
            tf   = cc['temp_F']
            feels_c = cc['FeelsLikeC']
            return f"{desc}, {tc}C/{tf}F, feels {feels_c}C"
        except Exception:
            return "Unavailable"

    def _asst_stock(self, ticker_or_name):
        import yfinance as yf
        NAME_MAP = {
            'apple': 'AAPL', 'google': 'GOOGL', 'alphabet': 'GOOGL',
            'microsoft': 'MSFT', 'amazon': 'AMZN', 'tesla': 'TSLA',
            'meta': 'META', 'facebook': 'META', 'netflix': 'NFLX',
            'nvidia': 'NVDA', 'reliance': 'RELIANCE.NS', 'infosys': 'INFY.NS',
            'tata': 'TCS.NS', 'wipro': 'WIPRO.NS',
        }
        ticker = NAME_MAP.get(ticker_or_name.lower(),
                              ticker_or_name.upper().replace(' ', '-'))
        try:
            info = yf.Ticker(ticker).fast_info
            price = info.last_price
            currency = getattr(info, 'currency', 'USD')
            return f"{currency} {price:.2f}" if price else "Not found"
        except Exception:
            return "Unavailable"

    def _asst_air_quality(self, city):
        import requests
        try:
            r = requests.get(
                f'https://api.openaq.org/v2/locations?city={city}&limit=1',
                timeout=5, headers={'Accept': 'application/json'})
            results = r.json().get('results', [])
            if not results:
                return "No data"
            loc_id = results[0]['id']
            r2 = requests.get(f'https://api.openaq.org/v2/latest/{loc_id}',
                              timeout=5, headers={'Accept': 'application/json'})
            measures = r2.json().get('results', [{}])[0].get('measurements', [])
            for m in measures:
                if m['parameter'] in ('pm25', 'pm2.5'):
                    val = m['value']
                    if val < 12:      cat = "Good"
                    elif val < 35.5:  cat = "Moderate"
                    elif val < 55.5:  cat = "Unhealthy*"
                    else:             cat = "Unhealthy"
                    return f"PM2.5={val:.0f} {cat}"
            return "No PM2.5 data"
        except Exception:
            return "Unavailable"

    def _asst_ollama(self, question):
        import requests
        host = os.environ.get('OLLAMA_HOST', '')
        if not host:
            return "Set OLLAMA_HOST env var (e.g. 192.168.1.10) for questions."
        model = os.environ.get('OLLAMA_MODEL', 'llama3.2')
        if ':' not in host:
            host = f"{host}:11434"
        url = f"http://{host}/api/chat"
        payload = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content":
                          f"Answer briefly in 1-2 sentences, no markdown: {question}"}],
        }
        try:
            r = requests.post(url, json=payload, timeout=15)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except Exception as e:
            return f"Ollama error: {str(e)[:55]}"

    def _asst_sanitise(self, text):
        """Strip characters the font can't render (emoji, degree symbol, etc.)."""
        return ''.join(c if 32 <= ord(c) < 127 else ' ' for c in text).strip()

    def _asst_wrap(self, text, width=14):
        words = text.split()
        lines, current = [], ''
        for word in words:
            if not current:
                current = word[:width]
            elif len(current) + 1 + len(word) <= width:
                current += ' ' + word
            else:
                lines.append(current)
                current = word[:width]
        if current:
            lines.append(current)
        return lines or ['(empty)']

    def ask_assistant(self, command):
        if self._asst_state == 'init':
            if not self._asst_loading:
                self._asst_loading = True
                threading.Thread(target=self._asst_load_whisper, daemon=True).start()
            return "Loading...", "Please wait"

        elif self._asst_state == 'idle':
            if command == 'yes':
                self._asst_scroll = 0
                self._asst_transcript = ''
                self._asst_lines = []
                self._asst_start_time = time.time()
                self._asst_state = 'listening'
                threading.Thread(target=self._asst_record_and_process,
                                 daemon=True).start()
            return "Press YES", "YES=ask"

        elif self._asst_state == 'listening':
            remaining = max(0, int(6 - (time.time() - self._asst_start_time)))
            return "Listening...", f"Rec {remaining}s left"

        elif self._asst_state == 'processing':
            q = self._asst_transcript
            short = (q[:11] + '..') if len(q) > 13 else q
            return short or '...', "Thinking..."

        elif self._asst_state == 'showing':
            if command == 'no':
                max_s = max(0, len(self._asst_lines) - 4)
                if self._asst_scroll >= max_s:
                    self._asst_scroll = 0
                else:
                    self._asst_scroll += 1
            elif command == 'yes':
                self._asst_state = 'idle'
                return "Press YES", "YES=ask"
            return '__showing__', ''

        return '...', ''

    # ── End voice assistant ────────────────────────────────────────────────────

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
