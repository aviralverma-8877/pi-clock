# Quick Start: Debian Package

## Install

```bash
wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.3/pi-clock_2.0.3_all.deb
sudo dpkg -i pi-clock_2.0.3_all.deb
sudo apt-get install -f
```

During installation you will be asked to choose an AI backend for the Voice Assistant — Gemini, Ollama, or disabled. You can change this later by editing `/opt/pi-clock/pi_clock.service`.

## Service Management

```bash
# Status
sudo systemctl status pi_clock.service

# Live logs
journalctl -u pi_clock.service -f

# Restart
sudo systemctl restart pi_clock.service

# Stop
sudo systemctl stop pi_clock.service
```

## Change AI Backend After Install

```bash
sudo nano /opt/pi-clock/pi_clock.service
# Set ASST_BACKEND=gemini or ollama, fill in the relevant key/host
sudo systemctl daemon-reload && sudo systemctl restart pi_clock.service
```

## Uninstall

```bash
sudo dpkg -r pi-clock      # remove
sudo dpkg -P pi-clock      # purge (removes config too)
```

## Build from Source

```bash
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock
./build-deb.sh
sudo dpkg -i pi-clock_2.0.3_all.deb
sudo apt-get install -f
```

## Hardware Setup

Connect the Nokia 5110 LCD and buttons according to the pin diagram in [README.md](README.md).

## Troubleshooting

**Service won't start?**
```bash
journalctl -u pi_clock.service -n 50
sudo raspi-config nonint do_spi 0 && sudo reboot
```

**Missing Python package?**
```bash
pip3 install --break-system-packages adafruit-circuitpython-pcd8544 faster-whisper sounddevice yfinance requests
sudo systemctl restart pi_clock.service
```

For more details, see [DEBIAN-PACKAGE.md](DEBIAN-PACKAGE.md) and [INSTALL-TROUBLESHOOTING.md](INSTALL-TROUBLESHOOTING.md).
