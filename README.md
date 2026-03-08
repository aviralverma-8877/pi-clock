# pi-clock

A Nokia 5110 LCD-based system monitor and clock for Raspberry Pi with interactive button controls.

## Features

- **Real-time Clock**: Display time in 24-hour or AM/PM format
- **System Monitoring**: View CPU, RAM, disk usage, and temperature
- **Network Status**: Check IP address and connection status
- **System Management**:
  - Update/upgrade packages
  - Adjust display contrast and backlight
  - Control system volume
  - Shutdown/restart system
- **Interactive Controls**: Four buttons for navigation and selection

## Hardware Requirements

- **Raspberry Pi** (Tested on Pi 3/4/5)
- **Nokia 5110 LCD Display** (PCD8544 controller)
- **4 Push Buttons** for navigation
- **Connecting Wires**

### Pin Connections

| Component | GPIO Pin | Physical Pin |
|-----------|----------|--------------|
| LCD SCLK  | GPIO 11  | Pin 23       |
| LCD DIN   | GPIO 10  | Pin 19       |
| LCD DC    | GPIO 23  | Pin 16       |
| LCD CS    | GPIO 8   | Pin 24       |
| LCD RST   | GPIO 24  | Pin 18       |
| LCD BL    | GPIO 22  | Pin 15       |
| Button Prev | GPIO 27 | Pin 13      |
| Button Next | GPIO 18 | Pin 12      |
| Button Yes | GPIO 17 | Pin 11       |
| Button No | GPIO 25 | Pin 22       |

## Compatibility

- **Raspberry Pi OS**: Bookworm (Debian 12) and later
- **Raspberry Pi Models**: Pi 3, Pi 4, Pi 5, Pi Zero W/2W
- **Python**: 3.9+

### Raspberry Pi 5 Notes

The software is compatible with Raspberry Pi 5. The GPIO pins work the same way through the `gpiozero` library. Ensure SPI is enabled during installation.

## Installation

### Method 1: Debian Package (Recommended)

Download and install the .deb package:

```bash
# Download the latest release
wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.0/pi-clock_2.0.0_armhf.deb

# Install the package
sudo dpkg -i pi-clock_2.0.0_armhf.deb

# Install any missing dependencies
sudo apt-get install -f
```

The Debian package automatically handles:
- System package installation
- Python dependencies
- SPI interface configuration
- Systemd service setup and start

See [DEBIAN-PACKAGE.md](DEBIAN-PACKAGE.md) for building the package yourself.

### Method 2: Installation Script

Run the following command to install:

```bash
wget --no-check-certificate https://raw.githubusercontent.com/aviralverma-8877/pi-clock/master/install.sh && sudo chmod +x install.sh && sudo ./install.sh
```

The installation script will:
1. Update system packages
2. Install required Python dependencies
3. Enable SPI interface
4. Clone the repository
5. Set up and start the systemd service

## Usage

After installation, the clock service will start automatically on boot.

### Service Management

```bash
# Check service status
sudo systemctl status pi_clock.service

# View logs
journalctl -u pi_clock.service -f

# Restart service
sudo systemctl restart pi_clock.service

# Stop service
sudo systemctl stop pi_clock.service

# Disable auto-start
sudo systemctl disable pi_clock.service
```

### Button Controls

- **Next/Prev**: Navigate through menu items
- **Yes/No**: Select options or toggle settings

### Menu Items

1. **Time**: Switch between 24-hour and 12-hour format
2. **Date**: Display current date and day
3. **Upgrade**: Check and install system updates
4. **Network**: View local IP address
5. **Temperature**: CPU temperature (toggle °C/°F)
6. **CPU**: Frequency and usage percentage
7. **RAM**: Memory usage statistics
8. **Disk**: Storage information
9. **Backlight**: Toggle LCD backlight on/off
10. **Contrast**: Adjust display contrast
11. **Volume**: Increase/decrease system volume
12. **Shutdown**: Power off the system
13. **Restart**: Reboot the system

## Troubleshooting

### Display not working
- Verify SPI is enabled: `sudo raspi-config nonint do_spi 0`
- Check wiring connections
- Verify display contrast settings

### Service fails to start
```bash
# Check logs for errors
journalctl -u pi_clock.service -n 50

# Common issues:
# - Missing dependencies: Run install.sh again
# - Permission errors: Ensure service runs as root
# - Hardware not connected: Check wiring
```

### Buttons not responding
- Verify GPIO pin connections
- Check button wiring (buttons should connect GPIO to Ground)
- Ensure pull-up resistors are configured (handled by gpiozero)

## Development

### Manual Installation

```bash
cd ~
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock

# Install dependencies
sudo apt install -y python3-pip python3-pil python3-psutil python3-gpiozero python3-apt
pip3 install --break-system-packages adafruit-circuitpython-pcd8544

# Enable SPI
sudo raspi-config nonint do_spi 0

# Run manually
sudo python3 main
```

## License

This project is open source. Feel free to modify and distribute.

## Credits

- Display Driver: Adafruit PCD8544 CircuitPython library
- Font: Enter Command (included)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
