# Quick Start: Debian Package

## For Package Users

### Install

```bash
# Download the package
wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.0/pi-clock_2.0.0_all.deb

# Install
sudo dpkg -i pi-clock_2.0.0_all.deb
sudo apt-get install -f
```

### Check Status

```bash
sudo systemctl status pi_clock.service
```

### View Live Logs

```bash
journalctl -u pi_clock.service -f
```

### Restart Service

```bash
sudo systemctl restart pi_clock.service
```

### Uninstall

```bash
# Remove package
sudo dpkg -r pi-clock

# Or completely purge
sudo dpkg -P pi-clock
```

## For Package Builders

### Build Package

```bash
# Clone repository
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock

# Build the .deb package
./build-deb.sh
```

### Test Package

```bash
# Install locally
sudo dpkg -i pi-clock_2.0.0_all.deb
sudo apt-get install -f

# Test functionality
sudo systemctl status pi_clock.service
journalctl -u pi_clock.service -n 50

# Test removal
sudo dpkg -r pi-clock
```

### Distribute

Upload `pi-clock_2.0.0_all.deb` to GitHub Releases or your own server.

## Hardware Setup

Connect the Nokia 5110 LCD and buttons according to the pin diagram in [README.md](README.md).

## Troubleshooting

**Service won't start?**
```bash
# Check logs
journalctl -u pi_clock.service -n 50

# Enable SPI if not enabled
sudo raspi-config nonint do_spi 0
sudo reboot
```

**Missing Python package?**
```bash
pip3 install --break-system-packages adafruit-circuitpython-pcd8544
sudo systemctl restart pi_clock.service
```

For more details, see [DEBIAN-PACKAGE.md](DEBIAN-PACKAGE.md).
