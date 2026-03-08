#!/usr/bin/env python3
"""
Diagnostic script for pi-clock
Tests display, buttons, and system components
"""

import time
import sys

print("=" * 50)
print("Pi-Clock Diagnostic Tool")
print("=" * 50)
print()

# Test 1: Import modules
print("Test 1: Checking Python modules...")
try:
    import board
    import busio
    import digitalio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_pcd8544
    import psutil
    from gpiozero import CPUTemperature
    print("  ✓ All modules imported successfully")
except ImportError as e:
    print(f"  ✗ Import error: {e}")
    print("  Run: pip3 install --break-system-packages adafruit-circuitpython-pcd8544")
    sys.exit(1)

# Test 2: Initialize SPI and display
print("\nTest 2: Initializing display...")
try:
    spi = busio.SPI(board.SCK, MOSI=board.MOSI)
    dc = digitalio.DigitalInOut(board.D23)
    cs = digitalio.DigitalInOut(board.CE0)
    reset = digitalio.DigitalInOut(board.D24)
    backlight = digitalio.DigitalInOut(board.D22)
    backlight.switch_to_output()
    backlight.value = True  # Turn on backlight

    display = adafruit_pcd8544.PCD8544(spi, dc, cs, reset)
    display.bias = 5
    display.contrast = 48
    display.invert = True
    display.fill(1)
    display.show()
    print("  ✓ Display initialized successfully")
except Exception as e:
    print(f"  ✗ Display error: {e}")
    print("  Check wiring and SPI configuration")
    sys.exit(1)

# Test 3: Initialize buttons
print("\nTest 3: Initializing buttons...")
try:
    prev_btn = digitalio.DigitalInOut(board.D27)
    next_btn = digitalio.DigitalInOut(board.D18)
    yes_btn = digitalio.DigitalInOut(board.D17)
    no_btn = digitalio.DigitalInOut(board.D25)

    prev_btn.switch_to_input(pull=digitalio.Pull.UP)
    next_btn.switch_to_input(pull=digitalio.Pull.UP)
    yes_btn.switch_to_input(pull=digitalio.Pull.UP)
    no_btn.switch_to_input(pull=digitalio.Pull.UP)
    print("  ✓ Buttons initialized successfully")
except Exception as e:
    print(f"  ✗ Button error: {e}")
    sys.exit(1)

# Test 4: Check button states
print("\nTest 4: Checking button states...")
print("  Button states (HIGH=not pressed, LOW=pressed):")
print(f"    Prev: {prev_btn.value}")
print(f"    Next: {next_btn.value}")
print(f"    Yes:  {yes_btn.value}")
print(f"    No:   {no_btn.value}")

if not prev_btn.value or not next_btn.value or not yes_btn.value or not no_btn.value:
    print("\n  ⚠ WARNING: One or more buttons appear to be pressed!")
    print("    This could cause the menu to auto-scroll.")
    print("    Check button wiring - buttons should connect GPIO to Ground")
    print("    Buttons should be open (not pressed) normally")

# Test 5: Display test pattern
print("\nTest 5: Displaying test pattern...")
try:
    image = Image.new('1', (display.width, display.height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, display.width-1, display.height-1), outline=0, fill=1)
    draw.rectangle((2, 2, display.width-3, display.height-3), outline=0, fill=1)
    draw.text((10, 10), "DIAG", fill=0)
    draw.text((10, 25), "TEST", fill=0)
    display.image(image)
    display.show()
    print("  ✓ Test pattern displayed")
    print("    You should see 'DIAG TEST' on the display")
except Exception as e:
    print(f"  ✗ Display test error: {e}")

# Test 6: Button press test
print("\nTest 6: Button press test (10 seconds)")
print("  Press each button and watch for detection...")
print("  Press Ctrl+C to exit early")

try:
    start_time = time.time()
    prev_state = (prev_btn.value, next_btn.value, yes_btn.value, no_btn.value)

    while time.time() - start_time < 10:
        current_state = (prev_btn.value, next_btn.value, yes_btn.value, no_btn.value)

        if current_state != prev_state:
            if not prev_btn.value:
                print("    PREV button pressed!")
            if not next_btn.value:
                print("    NEXT button pressed!")
            if not yes_btn.value:
                print("    YES button pressed!")
            if not no_btn.value:
                print("    NO button pressed!")
            prev_state = current_state

        time.sleep(0.05)

    print("  ✓ Button test complete")
except KeyboardInterrupt:
    print("\n  Button test interrupted")

# Test 7: System info
print("\nTest 7: System information...")
try:
    cpu = CPUTemperature()
    mem = psutil.virtual_memory()
    print(f"  CPU Temperature: {cpu.temperature:.1f}°C")
    print(f"  RAM Usage: {mem.percent}%")
    print("  ✓ System sensors working")
except Exception as e:
    print(f"  ✗ System info error: {e}")

# Test 8: Check if service is running
print("\nTest 8: Checking service status...")
import subprocess
try:
    result = subprocess.run(['systemctl', 'is-active', 'pi_clock.service'],
                          capture_output=True, text=True)
    if result.stdout.strip() == 'active':
        print("  ⚠ WARNING: pi_clock service is currently running!")
        print("    Stop it with: sudo systemctl stop pi_clock.service")
    else:
        print("  ✓ Service is not running (good for testing)")
except:
    pass

# Final summary
print("\n" + "=" * 50)
print("Diagnostic Summary")
print("=" * 50)

# Check for stuck buttons
stuck_buttons = []
if not prev_btn.value:
    stuck_buttons.append("PREV")
if not next_btn.value:
    stuck_buttons.append("NEXT")
if not yes_btn.value:
    stuck_buttons.append("YES")
if not no_btn.value:
    stuck_buttons.append("NO")

if stuck_buttons:
    print("\n⚠ PROBLEM FOUND:")
    print(f"  Buttons stuck/pressed: {', '.join(stuck_buttons)}")
    print("\nLikely causes:")
    print("  1. Button wiring is incorrect (should connect GPIO to GND)")
    print("  2. Buttons are wired backwards (normally-closed instead of normally-open)")
    print("  3. Physical button is stuck pressed")
    print("\nSolution:")
    print("  - Check each button connection")
    print("  - Buttons should be OPEN when not pressed")
    print("  - Press button to connect GPIO pin to Ground")
else:
    print("\n✓ All tests passed!")
    print("\nIf pi-clock still shows restart screen:")
    print("  1. Check logs: journalctl -u pi_clock.service -n 50")
    print("  2. Try running manually: sudo python3 /opt/pi-clock/main")
    print("  3. Check for hardware connection issues")

print("\nTo test manually (with service stopped):")
print("  sudo systemctl stop pi_clock.service")
print("  cd /opt/pi-clock")
print("  sudo python3 main")
print()
