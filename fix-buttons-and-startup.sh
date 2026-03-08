#!/bin/bash
# Quick fix script for pi-clock button issues
# This fixes the floating GPIO pins and ensures clock shows at startup

set -e

echo "Pi-Clock Button Fix Script"
echo "============================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Stop the service
echo "Stopping pi_clock service..."
systemctl stop pi_clock.service

# Backup original file
MAIN_FILE="/opt/pi-clock/main"
if [ ! -f "${MAIN_FILE}.backup" ]; then
    echo "Creating backup..."
    cp "$MAIN_FILE" "${MAIN_FILE}.backup"
    echo "  Backup saved to: ${MAIN_FILE}.backup"
fi

# Apply the fix
echo "Applying button pull-up fix..."

# Use sed to add pull-up resistors to button initialization
sed -i 's/prev_btn.switch_to_input()/prev_btn.switch_to_input(pull=digitalio.Pull.UP)/' "$MAIN_FILE"
sed -i 's/next_btn.switch_to_input()/next_btn.switch_to_input(pull=digitalio.Pull.UP)/' "$MAIN_FILE"
sed -i 's/yes_btn.switch_to_input()/yes_btn.switch_to_input(pull=digitalio.Pull.UP)/' "$MAIN_FILE"
sed -i 's/no_btn.switch_to_input()/no_btn.switch_to_input(pull=digitalio.Pull.UP)/' "$MAIN_FILE"

# Verify the fix was applied
if grep -q "pull=digitalio.Pull.UP" "$MAIN_FILE"; then
    echo "  ✓ Pull-up resistors added successfully"
else
    echo "  ✗ Failed to apply fix. Please apply manually."
    exit 1
fi

# Add a small startup delay to let buttons stabilize
echo "Adding startup stabilization delay..."
sed -i '/^print("Starting main loop...")/i # Allow buttons to stabilize\ntime.sleep(0.5)' "$MAIN_FILE"

echo ""
echo "Fix applied successfully!"
echo ""
echo "Restarting service..."
systemctl start pi_clock.service

# Wait a moment for service to start
sleep 2

# Check status
if systemctl is-active --quiet pi_clock.service; then
    echo "✓ Service is running"
    echo ""
    echo "Check the display - it should now show the Time (clock) screen"
    echo ""
    echo "View logs with: journalctl -u pi_clock.service -f"
else
    echo "✗ Service failed to start"
    echo ""
    echo "Check logs with: journalctl -u pi_clock.service -n 50"
fi

echo ""
echo "To restore original file if needed:"
echo "  sudo cp ${MAIN_FILE}.backup $MAIN_FILE"
echo "  sudo systemctl restart pi_clock.service"
