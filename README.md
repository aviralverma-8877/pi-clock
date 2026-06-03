# pi-clock

A Nokia 5110 LCD-based system monitor, clock, and voice assistant for Raspberry Pi with interactive button controls.

## Features

- **Real-time Clock**: Display time in 24-hour or AM/PM format
- **System Monitoring**: CPU, RAM, disk usage, and temperature
- **Network Status**: Local IP address and connection status
- **System Management**: Package updates, shutdown, restart
- **Display Controls**: Backlight toggle, contrast and volume adjustment
- **Voice Assistant** *(optional)*: Ask questions via USB microphone — powered by Gemini (Google) or Ollama (local/network LLM)
  - Weather by city
  - Stock prices
  - Air quality (PM2.5)
  - General Q&A via AI

## Hardware Requirements

- **Raspberry Pi** (Pi 3, 4, 5, Zero W/2W)
- **Nokia 5110 LCD Display** (PCD8544 controller)
- **4 Push Buttons** for navigation
- **USB Microphone** *(optional — required for Voice Assistant)*

### Pin Connections

| Component    | GPIO Pin | Physical Pin |
|--------------|----------|--------------|
| LCD SCLK     | GPIO 11  | Pin 23       |
| LCD DIN      | GPIO 10  | Pin 19       |
| LCD DC       | GPIO 23  | Pin 16       |
| LCD CS       | GPIO 8   | Pin 24       |
| LCD RST      | GPIO 24  | Pin 18       |
| LCD BL       | GPIO 22  | Pin 15       |
| Button Prev  | GPIO 27  | Pin 13       |
| Button Next  | GPIO 18  | Pin 12       |
| Button Yes   | GPIO 17  | Pin 11       |
| Button No    | GPIO 25  | Pin 22       |

## Compatibility

- **Raspberry Pi OS**: Bookworm (Debian 12) and later
- **Raspberry Pi Models**: Pi 3, Pi 4, Pi 5, Pi Zero W/2W
- **Python**: 3.9+

## Installation

### Method 1: Debian Package (Recommended)

```bash
wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.3/pi-clock_2.0.3_all.deb
sudo dpkg -i pi-clock_2.0.3_all.deb
sudo apt-get install -f
```

During installation you will be prompted to choose an AI backend for the Voice Assistant (Gemini, Ollama, or disabled).

See [DEBIAN-PACKAGE.md](DEBIAN-PACKAGE.md) for building the package yourself.

### Method 2: Install Script

```bash
wget --no-check-certificate https://raw.githubusercontent.com/aviralverma-8877/pi-clock/master/install.sh \
  && sudo chmod +x install.sh && sudo ./install.sh
```

**Troubleshooting**: See [INSTALL-TROUBLESHOOTING.md](INSTALL-TROUBLESHOOTING.md) if you hit dependency issues.

## Usage

The service starts automatically on boot.

### Button Controls

| Button | Action |
|--------|--------|
| **Next** | Scroll to next menu item |
| **Prev** | Scroll to previous menu item |
| **Yes** | Confirm / toggle / adjust up |
| **No** | Cancel / adjust down |

### Menu Items

| # | Screen | Yes | No |
|---|--------|-----|----|
| 1 | Time | Toggle 24hr/AM-PM | Toggle 24hr/AM-PM |
| 2 | Date | — | — |
| 3 | Upgrade | Refresh package list | Run full upgrade |
| 4 | Network | — | — |
| 5 | Temperature | Toggle °F | Toggle °C |
| 6 | CPU | — | — |
| 7 | RAM | — | — |
| 8 | Disk | — | — |
| 9 | Backlight | Turn on | Turn off |
| 10 | Contrast | Decrease | Increase |
| 11 | Volume | Volume up | Volume down |
| 12 | Shutdown | Confirm shutdown | — |
| 13 | Restart | Confirm restart | — |
| 14 | Assistant | Start listening / New question | Scroll answer down |

*Assistant menu only appears when `ASST_ENABLED=1` in the service file.*

### Service Management

```bash
sudo systemctl status pi_clock.service
sudo systemctl restart pi_clock.service
journalctl -u pi_clock.service -f
```

## Voice Assistant

The assistant uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (tiny.en model) for speech-to-text and routes general questions to your chosen AI backend.

### Backends

#### Gemini (Google AI)
Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey), then set:
```
Environment=ASST_BACKEND=gemini
Environment=GEMINI_API_KEY=your_key_here
Environment=GEMINI_MODEL=gemini-2.5-flash-lite
```

#### Ollama (Local / Network LLM)
Run [Ollama](https://ollama.ai) on any machine on your network, then set:
```
Environment=ASST_BACKEND=ollama
Environment=OLLAMA_HOST=192.168.1.x
Environment=OLLAMA_MODEL=llama3.2
```

### Configuring After Install

Edit the service file:
```bash
sudo nano /opt/pi-clock/pi_clock.service
sudo systemctl daemon-reload
sudo systemctl restart pi_clock.service
```

### How to Use the Assistant

1. Navigate to the **Assistant** screen
2. Press **YES** — recording starts (6 seconds)
3. Speak your question
4. Wait for the answer to appear
5. Press **NO** to scroll through longer answers
6. Press **YES** again to ask another question

### Special Queries

- *"Weather in London"* — current conditions and temperature
- *"Price of Apple"* / *"Stock price of TSLA"* — live stock price
- *"Air quality in Delhi"* — PM2.5 reading and category
- Anything else — routed to your AI backend

## Troubleshooting

### Display stuck or menu auto-scrolling

Symptom: display shows "Restart" on boot, or menu scrolls on its own.

This was a pull-up resistor bug fixed in v2.0.1. See [BUTTON-FIX-README.md](BUTTON-FIX-README.md).

### Display not working

```bash
sudo raspi-config nonint do_spi 0
sudo reboot
```

### Service fails to start

```bash
journalctl -u pi_clock.service -n 50
```

Common causes: missing dependencies, hardware not connected, SPI not enabled.

### Assistant not responding / "Set GEMINI_API_KEY"

Check that `ASST_BACKEND`, `GEMINI_API_KEY` (or `OLLAMA_HOST`), and `ASST_ENABLED=1` are all set in `/opt/pi-clock/pi_clock.service`.

### Buttons not responding

- Verify GPIO wiring (buttons connect GPIO to Ground)
- Run: `sudo python3 /opt/pi-clock/diagnose.py`

## Development

### Manual Setup

```bash
cd ~
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock

sudo apt install -y python3-pip python3-pil python3-psutil python3-gpiozero python3-apt libportaudio2
pip3 install --break-system-packages adafruit-circuitpython-pcd8544 faster-whisper sounddevice yfinance requests

sudo raspi-config nonint do_spi 0
sudo python3 main
```

### Building the Debian Package

```bash
./build-deb.sh
```

See [DEBIAN-PACKAGE.md](DEBIAN-PACKAGE.md) for details.

## License

Open source — free to modify and distribute.

## Credits

- Display driver: [Adafruit PCD8544 CircuitPython](https://github.com/adafruit/Adafruit_CircuitPython_PCD8544)
- Speech-to-text: [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Font: Enter Command (included)
