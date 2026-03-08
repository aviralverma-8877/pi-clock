# Installation Troubleshooting Guide

This guide helps resolve common installation issues with the pi-clock Debian package.

## Common Installation Errors

### Error: "Unsatisfied dependencies"

```
Unsatisfied dependencies:
 pi-clock:armhf : Depends: python3:armhf (>= 3.9) but it is not going to be installed
```

**Solution**: This error occurred with older versions using architecture-specific dependencies. The package has been updated to use `Architecture: all`.

**Steps to fix:**

1. **Remove old package** (if installed):
   ```bash
   sudo dpkg -r pi-clock
   ```

2. **Download the latest package** (v2.0.0 or newer with `_all.deb` suffix):
   ```bash
   wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.0/pi-clock_2.0.0_all.deb
   ```

3. **Install the new package**:
   ```bash
   sudo dpkg -i pi-clock_2.0.0_all.deb
   ```

4. **Install missing dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -f
   ```

### Error: "python3-pip is not installable"

On some Raspberry Pi OS versions, `python3-pip` may not be available as a package.

**Solution**: The package has been updated to list `python3-pip` as a recommendation (not a hard requirement).

**If pip3 is needed**, install it manually:
```bash
# Method 1: Using apt (if available)
sudo apt-get install python3-pip

# Method 2: Using get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python3 get-pip.py
rm get-pip.py

# Verify installation
pip3 --version
```

### Error: "Unable to locate package"

If you get an error about being unable to locate the package:

```bash
# Update package lists
sudo apt-get update

# Try installing dependencies manually
sudo apt-get install python3 python3-pil python3-psutil python3-gpiozero python3-apt

# Then install pi-clock
sudo dpkg -i pi-clock_2.0.0_all.deb
```

### Error: "adafruit-circuitpython-pcd8544 installation failed"

The postinst script tries to install this Python package automatically. If it fails:

**Manual installation:**
```bash
# Try with --break-system-packages (Debian Bookworm and later)
pip3 install --break-system-packages adafruit-circuitpython-pcd8544

# Or without (older systems)
pip3 install adafruit-circuitpython-pcd8544

# If pip3 is not found, install it first
sudo apt-get install python3-pip
```

### Error: "Service failed to start"

If the service installs but won't start:

**Check logs:**
```bash
journalctl -u pi_clock.service -n 50
```

**Common causes:**

1. **Hardware not connected**
   - Verify Nokia 5110 LCD is connected
   - Check all pin connections match the documentation

2. **SPI not enabled**
   ```bash
   # Enable SPI
   sudo raspi-config nonint do_spi 0

   # Reboot
   sudo reboot

   # After reboot, verify SPI is enabled
   lsmod | grep spi
   ```

3. **Permission issues**
   ```bash
   # The service runs as root, so this is usually not an issue
   # But verify the service file
   cat /etc/systemd/system/pi_clock.service
   ```

4. **Missing Python dependencies**
   ```bash
   # Test manually
   cd /opt/pi-clock
   sudo python3 main

   # Install any missing packages reported
   ```

## Architecture-Specific Issues

### Why "all" instead of "armhf"?

The package uses `Architecture: all` because:
- It's pure Python code (no compiled binaries)
- Works on both 32-bit (armhf) and 64-bit (arm64) Raspberry Pi OS
- Avoids architecture-specific dependency conflicts

### What if I have an older armhf package?

If you installed an older version with `_armhf.deb`:

1. **Remove old version:**
   ```bash
   sudo dpkg -r pi-clock
   ```

2. **Clean up:**
   ```bash
   sudo apt-get autoremove
   sudo apt-get clean
   ```

3. **Install new version:**
   ```bash
   sudo dpkg -i pi-clock_2.0.0_all.deb
   sudo apt-get install -f
   ```

## Raspberry Pi OS Specific Issues

### Bookworm (Debian 12) and later

**PEP 668 externally-managed-environment:**

Raspberry Pi OS Bookworm enforces PEP 668, which prevents pip from installing packages system-wide.

**Solutions:**

1. **Use --break-system-packages flag** (used by the package):
   ```bash
   pip3 install --break-system-packages adafruit-circuitpython-pcd8544
   ```

2. **Use virtual environment** (for manual testing):
   ```bash
   python3 -m venv ~/pi-clock-env
   source ~/pi-clock-env/bin/activate
   pip3 install adafruit-circuitpython-pcd8544
   ```

### Bullseye (Debian 11) and earlier

No special considerations. Standard pip installation works:
```bash
pip3 install adafruit-circuitpython-pcd8544
```

## Complete Fresh Installation

If you're having persistent issues, try a complete fresh installation:

```bash
# 1. Remove any existing installation
sudo systemctl stop pi_clock.service 2>/dev/null || true
sudo dpkg -P pi-clock 2>/dev/null || true
sudo rm -rf /opt/pi-clock
sudo rm -f /etc/systemd/system/pi_clock.service

# 2. Update system
sudo apt-get update
sudo apt-get upgrade -y

# 3. Install dependencies
sudo apt-get install -y python3 python3-pil python3-psutil python3-gpiozero python3-apt python3-pip

# 4. Enable SPI
sudo raspi-config nonint do_spi 0

# 5. Install pi-clock
wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.0/pi-clock_2.0.0_all.deb
sudo dpkg -i pi-clock_2.0.0_all.deb
sudo apt-get install -f

# 6. Check status
sudo systemctl status pi_clock.service
```

## Verification Steps

After installation, verify everything is working:

```bash
# 1. Check service status
sudo systemctl status pi_clock.service

# 2. View logs
journalctl -u pi_clock.service -n 50

# 3. Check files
ls -la /opt/pi-clock/

# 4. Verify SPI
lsmod | grep spi

# 5. Test Python imports
python3 -c "import adafruit_pcd8544; print('OK')"
python3 -c "import psutil; print('OK')"
python3 -c "import gpiozero; print('OK')"
```

## Getting Help

If you're still having issues:

1. **Check GitHub Issues**: https://github.com/aviralverma-8877/pi-clock/issues
2. **Create new issue** with:
   - Raspberry Pi model
   - Raspberry Pi OS version: `cat /etc/os-release`
   - Python version: `python3 --version`
   - Full error message
   - Output of: `journalctl -u pi_clock.service -n 50`

## Manual Installation Alternative

If the Debian package continues to cause issues, use the installation script instead:

```bash
wget --no-check-certificate https://raw.githubusercontent.com/aviralverma-8877/pi-clock/master/install.sh
sudo chmod +x install.sh
sudo ./install.sh
```

This script handles all dependencies and configuration automatically.
