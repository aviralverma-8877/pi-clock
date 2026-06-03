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

# Configure SPI with spi0-0cs overlay so GPIO 8 (CE0) is free for software CS
echo "Configuring SPI interface..."
CONFIG_FILE=""
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE="/boot/config.txt"
fi

if [ -n "$CONFIG_FILE" ]; then
    if grep -q "dtparam=spi=on" "$CONFIG_FILE"; then
        sed -i 's/dtparam=spi=on/dtoverlay=spi0-0cs/' "$CONFIG_FILE"
    elif ! grep -q "dtoverlay=spi0-0cs" "$CONFIG_FILE"; then
        echo "dtoverlay=spi0-0cs" >> "$CONFIG_FILE"
    fi
    echo "Note: A reboot is required for SPI changes to take effect."
else
    echo "Warning: Could not find config.txt. Please add 'dtoverlay=spi0-0cs' manually."
fi
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

# --- Assistant configuration ---
echo ""
echo "=== Assistant Configuration ==="
echo "Which AI backend do you want to use?"
echo "  1. Ollama (local/network server)"
echo "  2. Gemini (Google API)"
echo "  3. Disable Assistant"
printf "Select [1]: "
read ASST_CHOICE </dev/tty
ASST_CHOICE=${ASST_CHOICE:-1}

if [ "$ASST_CHOICE" = "3" ]; then
    echo "✓ Assistant disabled"
    sed -i "s|^Environment=ASST_ENABLED=.*|Environment=ASST_ENABLED=0|" pi_clock.service
    sed -i "s|^Environment=ASST_BACKEND=.*|Environment=ASST_BACKEND=ollama|" pi_clock.service
    sed -i "s|^Environment=OLLAMA_HOST=.*|Environment=OLLAMA_HOST=|" pi_clock.service
    sed -i "s|^Environment=GEMINI_API_KEY=.*|Environment=GEMINI_API_KEY=|" pi_clock.service

elif [ "$ASST_CHOICE" = "2" ]; then
    printf "Enter your Gemini API key: "
    read GEMINI_KEY </dev/tty
    if [ -z "$GEMINI_KEY" ]; then
        echo "✗ No API key entered. Assistant disabled."
        sed -i "s|^Environment=ASST_ENABLED=.*|Environment=ASST_ENABLED=0|" pi_clock.service
    else
        printf "Gemini model [gemini-1.5-flash]: "
        read GEMINI_MDL </dev/tty
        GEMINI_MDL=${GEMINI_MDL:-gemini-1.5-flash}
        echo "✓ Backend  : Gemini"
        echo "✓ Model    : ${GEMINI_MDL}"
        sed -i "s|^Environment=ASST_ENABLED=.*|Environment=ASST_ENABLED=1|" pi_clock.service
        sed -i "s|^Environment=ASST_BACKEND=.*|Environment=ASST_BACKEND=gemini|" pi_clock.service
        sed -i "s|^Environment=GEMINI_API_KEY=.*|Environment=GEMINI_API_KEY=${GEMINI_KEY}|" pi_clock.service
        sed -i "s|^Environment=GEMINI_MODEL=.*|Environment=GEMINI_MODEL=${GEMINI_MDL}|" pi_clock.service
        sed -i "s|^Environment=OLLAMA_HOST=.*|Environment=OLLAMA_HOST=|" pi_clock.service
    fi

else
    # Ollama (default)
    printf "Enter Ollama server IP or host:port (e.g. 192.168.1.30)\nPress Enter to disable Assistant: "
    read OLLAMA_HOST_INPUT </dev/tty
    if [ -z "$OLLAMA_HOST_INPUT" ]; then
        echo "✓ Assistant disabled"
        sed -i "s|^Environment=ASST_ENABLED=.*|Environment=ASST_ENABLED=0|" pi_clock.service
        sed -i "s|^Environment=OLLAMA_HOST=.*|Environment=OLLAMA_HOST=|" pi_clock.service
    else
        if echo "$OLLAMA_HOST_INPUT" | grep -q ":"; then
            OLLAMA_URL="http://${OLLAMA_HOST_INPUT}"
        else
            OLLAMA_URL="http://${OLLAMA_HOST_INPUT}:11434"
        fi
        echo "Fetching available models from ${OLLAMA_URL}..."
        MODELS_JSON=$(curl -sf --connect-timeout 5 "${OLLAMA_URL}/api/tags" 2>/dev/null || echo "")
        if [ -z "$MODELS_JSON" ]; then
            echo "Warning: Could not reach Ollama server."
            printf "Enter model name manually [deepseek-coder-v2:latest]: "
            read OLLAMA_MODEL_FINAL </dev/tty
            OLLAMA_MODEL_FINAL=${OLLAMA_MODEL_FINAL:-deepseek-coder-v2:latest}
        else
            MODEL_LIST=$(echo "$MODELS_JSON" | python3 -c "
import sys, json
models = [m['name'] for m in json.load(sys.stdin).get('models', [])]
for i, m in enumerate(models, 1):
    print(f'  {i}. {m}')
" 2>/dev/null)
            MODEL_COUNT=$(echo "$MODELS_JSON" | python3 -c "
import sys, json
print(len(json.load(sys.stdin).get('models', [])))
" 2>/dev/null)
            if [ -z "$MODEL_LIST" ] || [ "$MODEL_COUNT" = "0" ]; then
                printf "Enter model name manually [deepseek-coder-v2:latest]: "
                read OLLAMA_MODEL_FINAL </dev/tty
                OLLAMA_MODEL_FINAL=${OLLAMA_MODEL_FINAL:-deepseek-coder-v2:latest}
            else
                echo ""
                echo "Available models:"
                echo "$MODEL_LIST"
                printf "Select model number [1]: "
                read MODEL_SEL </dev/tty
                MODEL_SEL=${MODEL_SEL:-1}
                OLLAMA_MODEL_FINAL=$(echo "$MODELS_JSON" | python3 -c "
import sys, json
models = [m['name'] for m in json.load(sys.stdin).get('models', [])]
try:
    print(models[int('${MODEL_SEL}') - 1])
except:
    print(models[0])
" 2>/dev/null)
            fi
        fi
        echo "✓ Backend  : Ollama"
        echo "✓ Server   : ${OLLAMA_HOST_INPUT}"
        echo "✓ Model    : ${OLLAMA_MODEL_FINAL}"
        sed -i "s|^Environment=ASST_ENABLED=.*|Environment=ASST_ENABLED=1|" pi_clock.service
        sed -i "s|^Environment=ASST_BACKEND=.*|Environment=ASST_BACKEND=ollama|" pi_clock.service
        sed -i "s|^Environment=OLLAMA_HOST=.*|Environment=OLLAMA_HOST=${OLLAMA_HOST_INPUT}|" pi_clock.service
        sed -i "s|^Environment=OLLAMA_MODEL=.*|Environment=OLLAMA_MODEL=${OLLAMA_MODEL_FINAL}|" pi_clock.service
        sed -i "s|^Environment=GEMINI_API_KEY=.*|Environment=GEMINI_API_KEY=|" pi_clock.service
    fi
fi

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