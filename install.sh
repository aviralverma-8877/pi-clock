#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

echo "Installing pi-clock for Raspberry Pi OS (Bookworm compatible)..."

cd ~

# Update package lists
echo "Updating package lists..."
apt update -y
apt autoremove -y

# Install system dependencies
echo "Installing system dependencies..."
apt install -y git python3-pip python3-pil python3-dev python3-psutil python3-gpiozero

# Install Python packages with proper error handling
echo "Installing Python packages..."
pip3 install --break-system-packages adafruit-circuitpython-pcd8544 || {
    echo "Error installing adafruit-circuitpython-pcd8544"
    exit 1
}

# Install python-apt from system packages instead of pip
apt install -y python3-apt

# Enable SPI interface
echo "Enabling SPI interface..."
raspi-config nonint do_spi 0
DIR="pi-clock"
if [ -d "$DIR" ]; then
   echo "Removing existing pi-clock directory..."
   systemctl stop pi_clock.service 2>/dev/null || true
   rm -rf "$DIR"
fi

echo "Cloning pi-clock repository..."
git clone https://github.com/aviralverma-8877/pi-clock.git || {
    echo "Error cloning repository"
    exit 1
}

cd pi-clock

# Set proper permissions
chmod 755 pi_clock.service
chmod +x main

# Install systemd service
echo "Installing systemd service..."
SERVICE_FILE="/etc/systemd/system/pi_clock.service"
if [ -f "$SERVICE_FILE" ]; then
   rm "$SERVICE_FILE"
fi

ln -s "$PWD/pi_clock.service" "$SERVICE_FILE"

# Reload systemd and start service
echo "Starting pi_clock service..."
systemctl daemon-reload
systemctl enable pi_clock.service
systemctl start pi_clock.service

# Check service status
if systemctl is-active --quiet pi_clock.service; then
    echo "✓ pi-clock installed and running successfully!"
    echo "  Use 'systemctl status pi_clock.service' to check status"
    echo "  Use 'journalctl -u pi_clock.service -f' to view logs"
else
    echo "✗ Service failed to start. Check logs with:"
    echo "  journalctl -u pi_clock.service -n 50"
fi

# Clean up install script
cd ~
rm -f install.sh

echo "Installation complete!"