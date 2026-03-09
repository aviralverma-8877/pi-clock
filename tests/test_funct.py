"""
Unit tests for functions/funct.py

All hardware dependencies (GPIO, display, gpiozero, psutil, apt, socket)
are mocked so tests run without Raspberry Pi hardware.
"""

import sys
import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

# ---------------------------------------------------------------------------
# Mock all hardware/system modules before importing funct
# ---------------------------------------------------------------------------
gpiozero_mock = MagicMock()
sys.modules.setdefault("gpiozero", gpiozero_mock)
sys.modules.setdefault("adafruit_pcd8544", MagicMock())
sys.modules.setdefault("board", MagicMock())
sys.modules.setdefault("busio", MagicMock())
sys.modules.setdefault("digitalio", MagicMock())
apt_mock = MagicMock()
sys.modules.setdefault("apt", apt_mock)
sys.modules.setdefault("apt.progress", MagicMock())

import functions.funct as funct_module
from functions.funct import function, initialize_cache


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_btn(value=True):
    """Return a mock button. value=True means not pressed (pull-up)."""
    b = MagicMock()
    b.value = value
    return b


def make_display(contrast=48):
    d = MagicMock()
    d.contrast = contrast
    d.invert = True
    return d


def make_bkled(value=False):
    b = MagicMock()
    b.value = value
    return b


def make_function(contrast=48, bkled_value=False):
    prev_btn = make_btn()
    next_btn = make_btn()
    yes_btn  = make_btn()
    no_btn   = make_btn()
    bkled    = make_bkled(bkled_value)
    disp     = make_display(contrast)
    return function(prev_btn, next_btn, yes_btn, no_btn, bkled, disp, contrast)


# ---------------------------------------------------------------------------
# initialize_cache
# ---------------------------------------------------------------------------

class TestInitializeCache:
    def setup_method(self):
        # Reset module-level globals before each test
        funct_module.CACHE = None
        funct_module.TOTAL_PKG = 0
        funct_module.UPGRADABLE_PKG = 0
        funct_module.CACHE_INITIALIZED = False

    def test_returns_true_when_already_initialized(self):
        funct_module.CACHE_INITIALIZED = True
        assert initialize_cache() is True

    def test_counts_total_and_upgradable_packages(self):
        pkg_upgradable = MagicMock()
        pkg_upgradable.is_upgradable = True
        pkg_normal = MagicMock()
        pkg_normal.is_upgradable = False

        mock_cache = MagicMock()
        mock_cache.__iter__ = MagicMock(return_value=iter([pkg_upgradable, pkg_normal, pkg_normal]))

        with patch("functions.funct.apt") as mock_apt:
            mock_apt.Cache.return_value = mock_cache
            result = initialize_cache()

        assert result is True
        assert funct_module.TOTAL_PKG == 3
        assert funct_module.UPGRADABLE_PKG == 1
        assert funct_module.CACHE_INITIALIZED is True

    def test_returns_false_on_exception(self):
        with patch("functions.funct.apt") as mock_apt:
            mock_apt.Cache.side_effect = Exception("no apt")
            result = initialize_cache()

        assert result is False
        assert funct_module.CACHE_INITIALIZED is False


# ---------------------------------------------------------------------------
# toggleBkled
# ---------------------------------------------------------------------------

class TestToggleBkled:
    def test_comm_no_turns_backlight_on(self):
        fn = make_function()
        msg, body = fn.toggleBkled("no")
        assert fn.bkled.value is True
        assert msg == "  ON"
        assert body == "OFF           ON"

    def test_comm_yes_turns_backlight_off(self):
        fn = make_function(bkled_value=True)
        msg, body = fn.toggleBkled("yes")
        assert fn.bkled.value is False
        assert msg == "  OFF"
        assert body == "OFF           ON"

    def test_other_comm_reports_on_when_backlight_is_on(self):
        fn = make_function(bkled_value=True)
        fn.bkled.value = True
        msg, body = fn.toggleBkled("other")
        assert msg == "  ON"
        assert body == "OFF           ON"

    def test_other_comm_reports_off_when_backlight_is_off(self):
        fn = make_function(bkled_value=False)
        fn.bkled.value = False
        msg, body = fn.toggleBkled("other")
        assert msg == "  OFF"
        assert body == "OFF           ON"


# ---------------------------------------------------------------------------
# get_time
# ---------------------------------------------------------------------------

class TestGetTime:
    def test_comm_no_returns_12hr_format(self):
        fn = make_function()
        msg, body = fn.get_time("no")
        # 12-hr format includes AM/PM
        assert "AM" in msg.upper() or "PM" in msg.upper()
        assert body == "24hr      am/pm"

    def test_comm_yes_returns_24hr_format(self):
        fn = make_function()
        msg, body = fn.get_time("yes")
        # 24-hr format: HH:MM:SS, no AM/PM
        assert "AM" not in msg.upper() and "PM" not in msg.upper()
        assert len(msg) == 8  # HH:MM:SS
        assert body == "24hr      am/pm"

    def test_format_persists_across_calls(self):
        fn = make_function()
        fn.get_time("yes")          # switch to 24hr
        msg, _ = fn.get_time("other")  # should stay 24hr
        assert "AM" not in msg.upper() and "PM" not in msg.upper()

    def test_default_format_is_12hr(self):
        fn = make_function()
        # _time_format starts as "no" → 12hr
        msg, _ = fn.get_time("other")
        assert "AM" in msg.upper() or "PM" in msg.upper()


# ---------------------------------------------------------------------------
# get_date
# ---------------------------------------------------------------------------

class TestGetDate:
    def test_returns_date_and_weekday(self):
        from datetime import datetime
        fn = make_function()
        msg, body = fn.get_date("no")
        now = datetime.now()
        assert now.strftime("%d-%m-%Y") in msg
        assert now.strftime("%A") == body


# ---------------------------------------------------------------------------
# get_disk
# ---------------------------------------------------------------------------

class TestGetDisk:
    def test_returns_free_and_total(self):
        mock_disk = MagicMock()
        mock_disk.free  = 10 * (1024 ** 3)   # 10 GB
        mock_disk.total = 32 * (1024 ** 3)   # 32 GB

        fn = make_function()
        with patch("functions.funct.psutil.disk_usage", return_value=mock_disk):
            msg, body = fn.get_disk("no")

        assert "10.0" in msg
        assert "32.0" in body

    def test_format_strings(self):
        mock_disk = MagicMock()
        mock_disk.free  = 5.5 * (1024 ** 3)
        mock_disk.total = 16.0 * (1024 ** 3)

        fn = make_function()
        with patch("functions.funct.psutil.disk_usage", return_value=mock_disk):
            msg, body = fn.get_disk("no")

        assert msg.startswith("Free")
        assert body.startswith("Total")


# ---------------------------------------------------------------------------
# get_cpu
# ---------------------------------------------------------------------------

class TestGetCpu:
    def test_returns_freq_and_utilization(self):
        mock_freq = MagicMock()
        mock_freq.current = 1500.0

        fn = make_function()
        with patch("functions.funct.psutil.cpu_freq", return_value=mock_freq), \
             patch("functions.funct.psutil.cpu_percent", return_value=42.5):
            msg, body = fn.get_cpu("no")

        assert "1500" in msg
        assert "42.5" in body
        assert "MHz" in msg
        assert "Util" in body


# ---------------------------------------------------------------------------
# get_ram
# ---------------------------------------------------------------------------

class TestGetRam:
    def test_returns_free_used_total(self):
        mock_mem = MagicMock()
        mock_mem.free  = 512 * (1024 ** 2)   # 512 MB
        mock_mem.used  = 256 * (1024 ** 2)   # 256 MB
        mock_mem.total = 1024 * (1024 ** 2)  # 1024 MB

        fn = make_function()
        with patch("functions.funct.psutil.virtual_memory", return_value=mock_mem):
            msg, body = fn.get_ram("no")

        assert "512.0" in msg
        assert "256.0" in msg
        assert "1024.0" in body
        assert "RAM" in body


# ---------------------------------------------------------------------------
# get_cpu_temperature
# ---------------------------------------------------------------------------

class TestGetCpuTemperature:
    def _mock_cpu_temp(self, temp_c):
        mock_cpu = MagicMock()
        type(mock_cpu).temperature = PropertyMock(return_value=temp_c)
        return mock_cpu

    def test_default_returns_celsius(self):
        fn = make_function()
        with patch("functions.funct.CPUTemperature", return_value=self._mock_cpu_temp(50.0)):
            msg, body = fn.get_cpu_temperature("other")
        assert "50.0 C" == msg
        assert body == "F              C"

    def test_comm_no_sets_celsius(self):
        fn = make_function()
        with patch("functions.funct.CPUTemperature", return_value=self._mock_cpu_temp(50.0)):
            msg, body = fn.get_cpu_temperature("no")
        assert "C" in msg
        assert "F" not in msg

    def test_comm_yes_sets_fahrenheit(self):
        fn = make_function()
        with patch("functions.funct.CPUTemperature", return_value=self._mock_cpu_temp(0.0)):
            msg, body = fn.get_cpu_temperature("yes")
        assert "32.0 F" == msg

    def test_fahrenheit_conversion(self):
        fn = make_function()
        with patch("functions.funct.CPUTemperature", return_value=self._mock_cpu_temp(100.0)):
            fn.get_cpu_temperature("yes")   # switch to F
        with patch("functions.funct.CPUTemperature", return_value=self._mock_cpu_temp(100.0)):
            msg, _ = fn.get_cpu_temperature("other")
        assert "212.0 F" == msg

    def test_format_persists_across_calls(self):
        fn = make_function()
        with patch("functions.funct.CPUTemperature", return_value=self._mock_cpu_temp(50.0)):
            fn.get_cpu_temperature("yes")
        with patch("functions.funct.CPUTemperature", return_value=self._mock_cpu_temp(50.0)):
            msg, _ = fn.get_cpu_temperature("other")
        assert "F" in msg


# ---------------------------------------------------------------------------
# get_ip
# ---------------------------------------------------------------------------

class TestGetIp:
    def test_returns_ip_when_connected(self):
        fn = make_function()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("192.168.1.10", 0)

        with patch("functions.funct.socket.socket", return_value=mock_sock):
            status, ip = fn.get_ip("no")

        assert status == "Local IP"
        assert ip == "192.168.1.10"

    def test_returns_link_down_when_disconnected(self):
        fn = make_function()
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("Network unreachable")

        with patch("functions.funct.socket.socket", return_value=mock_sock):
            status, ip = fn.get_ip("no")

        assert status == "Link Down"
        assert ip == "Not Available"

    def test_caches_result_within_5_seconds(self):
        fn = make_function()
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("10.0.0.1", 0)

        with patch("functions.funct.socket.socket", return_value=mock_sock):
            fn.get_ip("no")  # populate cache

        # Second call: socket should NOT be called again
        with patch("functions.funct.socket.socket", return_value=mock_sock) as mock_socket_cls:
            status, ip = fn.get_ip("no")
            mock_socket_cls.assert_not_called()

        assert ip == "10.0.0.1"

    def test_refreshes_cache_after_5_seconds(self):
        fn = make_function()
        fn._last_ip_check = time.time() - 6  # expired
        fn._cached_ip = "old"
        fn._cached_ip_status = "old"

        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("172.16.0.1", 0)

        with patch("functions.funct.socket.socket", return_value=mock_sock):
            status, ip = fn.get_ip("no")

        assert ip == "172.16.0.1"
        assert status == "Local IP"


# ---------------------------------------------------------------------------
# set_volume
# ---------------------------------------------------------------------------

class TestSetVolume:
    def test_comm_yes_increases_volume(self):
        fn = make_function()
        with patch("functions.funct.os.system") as mock_sys:
            msg, body = fn.set_volume("yes")
            mock_sys.assert_called_once_with("amixer sset PCM 5%+")
        assert body == "+              -"

    def test_comm_no_decreases_volume(self):
        fn = make_function()
        with patch("functions.funct.os.system") as mock_sys:
            msg, body = fn.set_volume("no")
            mock_sys.assert_called_once_with("amixer sset PCM 5%-")

    def test_other_comm_does_not_call_system(self):
        fn = make_function()
        with patch("functions.funct.os.system") as mock_sys:
            fn.set_volume("other")
            mock_sys.assert_not_called()

    def test_always_returns_button_labels(self):
        fn = make_function()
        with patch("functions.funct.os.system"):
            for comm in ("yes", "no", "other"):
                _, body = fn.set_volume(comm)
                assert body == "+              -"


# ---------------------------------------------------------------------------
# set_contrast
# ---------------------------------------------------------------------------

class TestSetContrast:
    def test_comm_yes_decreases_contrast(self):
        fn = make_function(contrast=50)
        fn.set_contrast("yes")
        assert fn.contrast == 49
        assert fn.disp.contrast == 49

    def test_comm_no_increases_contrast(self):
        fn = make_function(contrast=50)
        fn.set_contrast("no")
        assert fn.contrast == 51
        assert fn.disp.contrast == 51

    def test_lower_bound_not_exceeded(self):
        fn = make_function(contrast=40)
        fn.set_contrast("yes")   # at min, should not decrease
        assert fn.contrast == 40

    def test_upper_bound_not_exceeded(self):
        fn = make_function(contrast=70)
        fn.set_contrast("no")    # at max, should not increase
        assert fn.contrast == 70

    def test_returns_button_labels(self):
        fn = make_function(contrast=50)
        _, body = fn.set_contrast("yes")
        assert body == "+              -"

    def test_invert_stays_true_after_change(self):
        fn = make_function(contrast=50)
        fn.set_contrast("yes")
        assert fn.disp.invert is True


# ---------------------------------------------------------------------------
# shutdown
# ---------------------------------------------------------------------------

class TestShutdown:
    def test_initial_state_shows_yes_no_buttons(self):
        fn = make_function()
        msg, body = fn.shutdown("no")
        assert msg == ""
        assert body == "yes           no"

    def test_comm_yes_sets_last_comm_and_shows_wait(self):
        fn = make_function()
        with patch("functions.funct.os.system"), \
             patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            msg, body = fn.shutdown("yes")

        assert fn.last_comm == "shutdown"
        assert body == "yes         Wait.."
        assert msg == ""

    def test_comm_yes_spawns_background_thread(self):
        fn = make_function()
        with patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            fn.shutdown("yes")
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()

    def test_shutdown_command_not_called_immediately(self):
        """os.system should be called inside the thread, not directly."""
        fn = make_function()
        with patch("functions.funct.os.system") as mock_sys, \
             patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            fn.shutdown("yes")
            mock_sys.assert_not_called()  # not called before thread runs

    def test_idempotent_on_repeated_yes(self):
        """Second 'yes' should not start another thread."""
        fn = make_function()
        with patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            fn.shutdown("yes")
            fn.shutdown("yes")
            assert mock_thread.call_count == 1

    def test_already_shutting_down_shows_wait(self):
        fn = make_function()
        fn.last_comm = "shutdown"
        msg, body = fn.shutdown("no")
        assert body == "yes         Wait.."


# ---------------------------------------------------------------------------
# restart
# ---------------------------------------------------------------------------

class TestRestart:
    def test_initial_state_shows_yes_no_buttons(self):
        fn = make_function()
        msg, body = fn.restart("no")
        assert msg == ""
        assert body == "yes           no"

    def test_comm_yes_sets_last_comm_and_shows_wait(self):
        fn = make_function()
        with patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            msg, body = fn.restart("yes")

        assert fn.last_comm == "rebooting"
        assert body == "yes         Wait.."
        assert msg == ""

    def test_comm_yes_spawns_background_thread(self):
        fn = make_function()
        with patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            fn.restart("yes")
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()

    def test_reboot_command_not_called_immediately(self):
        fn = make_function()
        with patch("functions.funct.os.system") as mock_sys, \
             patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            fn.restart("yes")
            mock_sys.assert_not_called()

    def test_idempotent_on_repeated_yes(self):
        fn = make_function()
        with patch("functions.funct.threading.Thread") as mock_thread:
            mock_thread.return_value = MagicMock()
            fn.restart("yes")
            fn.restart("yes")
            assert mock_thread.call_count == 1

    def test_already_rebooting_shows_wait(self):
        fn = make_function()
        fn.last_comm = "rebooting"
        msg, body = fn.restart("no")
        assert body == "yes         Wait.."


# ---------------------------------------------------------------------------
# no_button_pressed
# ---------------------------------------------------------------------------

class TestNoButtonPressed:
    def test_returns_true_when_all_released(self):
        fn = make_function()
        fn.next_btn.value = True
        fn.prev_btn.value = True
        fn.yes_btn.value  = True
        fn.no_btn.value   = True
        assert fn.no_button_pressed() is True

    def test_returns_false_when_next_pressed(self):
        fn = make_function()
        fn.next_btn.value = False  # pressed
        assert fn.no_button_pressed() is False

    def test_returns_false_when_prev_pressed(self):
        fn = make_function()
        fn.prev_btn.value = False
        assert fn.no_button_pressed() is False

    def test_returns_false_when_yes_pressed(self):
        fn = make_function()
        fn.yes_btn.value = False
        assert fn.no_button_pressed() is False

    def test_returns_false_when_no_pressed(self):
        fn = make_function()
        fn.no_btn.value = False
        assert fn.no_button_pressed() is False


# ---------------------------------------------------------------------------
# alert
# ---------------------------------------------------------------------------

class TestAlert:
    def test_alert_when_backlight_is_on_ends_on(self):
        fn = make_function(bkled_value=True)
        fn.bkled.value = True
        with patch("functions.funct.time.sleep"):
            fn.alert()
        assert fn.bkled.value is True

    def test_alert_when_backlight_is_off_ends_off(self):
        fn = make_function(bkled_value=False)
        fn.bkled.value = False
        with patch("functions.funct.time.sleep"):
            fn.alert()
        assert fn.bkled.value is False

    def test_alert_toggles_backlight_multiple_times(self):
        fn = make_function()

        assigned = []

        class TrackedBkled:
            def __init__(self, initial):
                self._value = initial

            @property
            def value(self):
                return self._value

            @value.setter
            def value(self, v):
                self._value = v
                assigned.append(v)

        fn.bkled = TrackedBkled(True)

        with patch("functions.funct.time.sleep"):
            fn.alert()

        # Should toggle at least 3 times
        assert len(assigned) >= 3
