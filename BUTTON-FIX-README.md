# Button Fix: Stuck on Restart Screen

## Problem

After installation, the display immediately shows the "Restart" screen and won't respond to button presses, or it cycles through menus rapidly on its own.

## Root Cause

The GPIO pins for buttons were configured as inputs without pull-up resistors. This causes the pins to "float" (have undefined voltage levels), making them randomly read as pressed or not pressed.

**Technical Details:**
- Buttons connect GPIO pins to Ground (GND) when pressed
- Without pull-up resistors, the GPIO pins have no defined HIGH state
- Floating pins can randomly trigger button presses
- This causes the menu to auto-scroll to random positions

## Solution

The fix adds internal pull-up resistors to the GPIO pins, which:
- Keep pins at HIGH (3.3V) when buttons are not pressed
- Pull to LOW (0V/Ground) only when button is physically pressed
- Prevents floating pin behavior

## How to Apply the Fix

### Method 1: Update from Git (Recommended)

```bash
# Stop the service
sudo systemctl stop pi_clock.service

# Navigate to installation directory
cd /opt/pi-clock

# Backup current main file
sudo cp main main.backup

# Pull latest changes (if installed via git)
sudo git pull

# Or manually update the file - see below
```

### Method 2: Manual File Edit

```bash
# Stop the service
sudo systemctl stop pi_clock.service

# Edit the main file
sudo nano /opt/pi-clock/main

# Find these lines (around line 34-37):
prev_btn.switch_to_input()
next_btn.switch_to_input()
yes_btn.switch_to_input()
no_btn.switch_to_input()

# Replace with:
prev_btn.switch_to_input(pull=digitalio.Pull.UP)
next_btn.switch_to_input(pull=digitalio.Pull.UP)
yes_btn.switch_to_input(pull=digitalio.Pull.UP)
no_btn.switch_to_input(pull=digitalio.Pull.UP)

# Save: Ctrl+O, Enter, then exit: Ctrl+X
```

### Method 3: Download Fixed File

```bash
# Stop the service
sudo systemctl stop pi_clock.service

# Download the fixed main file
cd /opt/pi-clock
sudo mv main main.backup
sudo wget https://raw.githubusercontent.com/aviralverma-8877/pi-clock/master/main

# Make it executable
sudo chmod +x main
```

### Method 4: Reinstall Package

If you installed via .deb package:

```bash
# Remove old package
sudo dpkg -r pi-clock

# Download and install new package with fix
wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.1/pi-clock_2.0.1_all.deb
sudo dpkg -i pi-clock_2.0.1_all.deb
sudo apt-get install -f
```

## Restart the Service

After applying the fix:

```bash
# Restart the service
sudo systemctl restart pi_clock.service

# Check status
sudo systemctl status pi_clock.service

# View logs to confirm it's working
journalctl -u pi_clock.service -f
```

## Test the Fix

You should now see:
1. Display starts at "Time" menu (not Restart)
2. Buttons respond properly:
   - **Next**: Cycles forward through menu
   - **Prev**: Cycles backward through menu
   - **Yes/No**: Selects options or toggles settings
3. No random menu cycling

## Run Diagnostic Tool

To verify everything is working:

```bash
# Stop the service first
sudo systemctl stop pi_clock.service

# Run diagnostic
cd /opt/pi-clock
sudo python3 diagnose.py

# The diagnostic will check:
# - Button states
# - Display functionality
# - Button press detection
```

## Verify Button Wiring

Ensure your buttons are wired correctly:

```
Button Wiring (for each button):
┌─────────────┐
│   Button    │
└──┬────────┬─┘
   │        │
GPIO Pin   GND Pin

When NOT pressed: GPIO reads HIGH (3.3V via pull-up)
When pressed: GPIO reads LOW (connected to Ground)
```

**Correct connections:**
- Prev Button: One side to GPIO 27, other side to GND
- Next Button: One side to GPIO 18, other side to GND
- Yes Button: One side to GPIO 17, other side to GND
- No Button: One side to GPIO 25, other side to GND

## Still Having Issues?

If the problem persists after the fix:

### 1. Check Hardware Connections

```bash
# Run diagnostic to see button states
sudo systemctl stop pi_clock.service
cd /opt/pi-clock
sudo python3 diagnose.py
```

Look for:
- "⚠ WARNING: One or more buttons appear to be pressed!"
- This indicates wiring issues

### 2. Check for Stuck Buttons

- Physically check each button
- Ensure buttons are not mechanically stuck
- Verify buttons are normally-open type (not normally-closed)

### 3. View Logs

```bash
journalctl -u pi_clock.service -n 100
```

Look for:
- Errors during startup
- Repeated button press messages
- Hardware initialization errors

### 4. Test Manually

```bash
# Stop service
sudo systemctl stop pi_clock.service

# Run manually to see real-time output
cd /opt/pi-clock
sudo python3 main

# Watch for:
# - "Loading images..." (should complete)
# - "Starting main loop..." (should start)
# - No errors
```

Press Ctrl+C to stop.

### 5. Check SPI

```bash
# Verify SPI is enabled
ls /dev/spi*

# Should show: /dev/spidev0.0  /dev/spidev0.1

# If not found, enable SPI:
sudo raspi-config nonint do_spi 0
sudo reboot
```

## Technical Details

### What Changed

**Before (broken):**
```python
prev_btn.switch_to_input()
```

**After (fixed):**
```python
prev_btn.switch_to_input(pull=digitalio.Pull.UP)
```

### Why This Matters

Without `pull=digitalio.Pull.UP`:
- GPIO pin has no defined voltage when button is not pressed
- Pin "floats" between HIGH and LOW randomly
- Electrical noise can trigger false button presses
- Menu auto-scrolls uncontrollably

With `pull=digitalio.Pull.UP`:
- Internal ~50kΩ resistor connects pin to 3.3V
- Pin reliably reads HIGH when button not pressed
- Pin reads LOW only when button physically pressed
- Clean, predictable button behavior

## Prevention

This fix is now included in:
- Latest git repository
- Version 2.0.1+ of the .deb package
- Updated install.sh script

If you're installing fresh, ensure you're using the latest version to avoid this issue.

## Related Issues

- If buttons work but menu cycles too fast: Adjust UPDATE_INTERVAL in main (line 109)
- If buttons don't respond at all: Check wiring and GPIO pin numbers
- If display is blank: Check contrast setting and backlight connection

## Need More Help?

1. Run the diagnostic: `sudo python3 /opt/pi-clock/diagnose.py`
2. Check logs: `journalctl -u pi_clock.service -n 100`
3. Report issue: https://github.com/aviralverma-8877/pi-clock/issues

Include:
- Diagnostic output
- Log output
- Raspberry Pi model
- Pi OS version: `cat /etc/os-release`
