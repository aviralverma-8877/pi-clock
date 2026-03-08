# Building and Installing pi-clock Debian Package

This guide explains how to build and install pi-clock as a Debian package (.deb) for easy distribution and installation on Raspberry Pi.

## Benefits of Debian Package

- **Easy Installation**: Single command to install with all dependencies
- **Automatic Service Setup**: Systemd service is configured automatically
- **Clean Removal**: Properly uninstalls and cleans up all files
- **Dependency Management**: Automatically installs required packages
- **System Integration**: Follows Debian/Raspbian packaging standards

## Building the Package

### Prerequisites

On your build machine (can be the Raspberry Pi itself):

```bash
sudo apt-get install dpkg-dev build-essential
```

### Build Steps

1. Navigate to the pi-clock project directory:
   ```bash
   cd pi-clock
   ```

2. Run the build script:
   ```bash
   ./build-deb.sh
   ```

3. The script will create `pi-clock_2.0.0_armhf.deb` in the current directory.

### Build Output

The build script will:
- Create the package directory structure
- Copy all necessary files
- Set proper permissions
- Generate the .deb package
- Display package information and installation instructions

## Installing the Package

### On Raspberry Pi

1. Transfer the .deb file to your Raspberry Pi (if built elsewhere):
   ```bash
   scp pi-clock_2.0.0_armhf.deb pi@raspberrypi.local:~
   ```

2. Install the package:
   ```bash
   sudo dpkg -i pi-clock_2.0.0_armhf.deb
   ```

3. If there are missing dependencies, install them:
   ```bash
   sudo apt-get install -f
   ```

### What Happens During Installation

The package will automatically:
1. Install files to `/opt/pi-clock/`
2. Install required system packages
3. Install Python packages (adafruit-circuitpython-pcd8544)
4. Enable SPI interface
5. Create systemd service symlink
6. Enable and start the pi_clock service

## Managing the Installed Service

### Check Status
```bash
sudo systemctl status pi_clock.service
```

### View Logs
```bash
journalctl -u pi_clock.service -f
```

### Stop Service
```bash
sudo systemctl stop pi_clock.service
```

### Start Service
```bash
sudo systemctl start pi_clock.service
```

### Restart Service
```bash
sudo systemctl restart pi_clock.service
```

### Disable Auto-start
```bash
sudo systemctl disable pi_clock.service
```

### Enable Auto-start
```bash
sudo systemctl enable pi_clock.service
```

## Removing the Package

### Standard Removal
Removes the package but keeps configuration files:
```bash
sudo dpkg -r pi-clock
```

### Complete Removal (Purge)
Removes everything including configuration:
```bash
sudo dpkg -P pi-clock
```

Or using apt:
```bash
sudo apt-get purge pi-clock
```

## Package Structure

```
pi-clock_2.0.0_armhf.deb
├── DEBIAN/
│   ├── control          # Package metadata and dependencies
│   ├── postinst         # Post-installation script
│   ├── prerm            # Pre-removal script
│   └── postrm           # Post-removal script
└── opt/
    └── pi-clock/
        ├── main         # Main Python application
        ├── functions/   # Python function modules
        ├── images/      # LCD display images
        ├── fonts/       # Display fonts
        ├── pi_clock.service  # Systemd service file
        └── README.md    # Documentation
```

## Customizing the Package

### Updating Version

Edit `build-deb.sh`:
```bash
VERSION="2.0.1"
```

Edit `debian/DEBIAN/control`:
```
Version: 2.0.1
```

### Changing Installation Path

By default, the package installs to `/opt/pi-clock/`. To change:

1. Edit `build-deb.sh`:
   ```bash
   PACKAGE_DIR="${BUILD_DIR}/usr/share/${PACKAGE_NAME}"
   ```

2. Update paths in `debian/DEBIAN/postinst`

3. Update `WorkingDirectory` and `ExecStart` in the systemd service file generation within `build-deb.sh`

### Adding Dependencies

Edit `debian/DEBIAN/control` and add to the `Depends:` line:
```
Depends: python3 (>= 3.9), python3-pil, python3-psutil, your-new-package
```

## Troubleshooting

### Build Fails

**Error: DEBIAN/control file not found**
- Ensure you're in the pi-clock root directory
- Check that `debian/DEBIAN/control` exists

**Permission denied**
- Make the build script executable: `chmod +x build-deb.sh`

### Installation Issues

**Missing dependencies**
```bash
sudo apt-get install -f
```

**Service fails to start**
```bash
# Check logs
journalctl -u pi_clock.service -n 50

# Common issues:
# - Hardware not connected
# - SPI not enabled
# - Permission issues
```

**SPI not enabled**
```bash
sudo raspi-config nonint do_spi 0
sudo reboot
```

## Distribution

### Creating a Repository

For easier distribution, create an APT repository:

1. Sign the package:
   ```bash
   dpkg-sig --sign builder pi-clock_2.0.0_armhf.deb
   ```

2. Create repository structure:
   ```bash
   mkdir -p repo/binary
   cp pi-clock_2.0.0_armhf.deb repo/binary/
   cd repo
   dpkg-scanpackages binary /dev/null | gzip -9c > binary/Packages.gz
   ```

3. Host the repository and users can add it:
   ```bash
   echo "deb [trusted=yes] http://your-server/repo binary/" | sudo tee /etc/apt/sources.list.d/pi-clock.list
   sudo apt update
   sudo apt install pi-clock
   ```

### GitHub Releases

Upload the .deb file to GitHub Releases for easy distribution:

1. Create a release on GitHub
2. Upload `pi-clock_2.0.0_armhf.deb`
3. Users can download and install:
   ```bash
   wget https://github.com/aviralverma-8877/pi-clock/releases/download/v2.0.0/pi-clock_2.0.0_armhf.deb
   sudo dpkg -i pi-clock_2.0.0_armhf.deb
   ```

## Package Testing

Before distribution, test the package thoroughly:

### Clean Installation Test
```bash
# On a fresh Raspberry Pi
sudo dpkg -i pi-clock_2.0.0_armhf.deb
sudo apt-get install -f
sudo systemctl status pi_clock.service
```

### Upgrade Test
```bash
# Install old version first, then new version
sudo dpkg -i pi-clock_1.0.0_armhf.deb
sudo dpkg -i pi-clock_2.0.0_armhf.deb
```

### Removal Test
```bash
sudo dpkg -r pi-clock
# Verify all services stopped and files removed (except config)
sudo dpkg -P pi-clock
# Verify complete removal
```

## Advanced: Multi-Architecture Support

To build for different Raspberry Pi architectures:

### For 64-bit Raspberry Pi OS (arm64)

Edit `build-deb.sh`:
```bash
ARCH="arm64"
```

Edit `debian/DEBIAN/control`:
```
Architecture: arm64
```

### For both architectures

Edit `debian/DEBIAN/control`:
```
Architecture: armhf arm64
```

Build separate packages for each architecture.

## License

This packaging configuration is part of the pi-clock project and follows the same license.

## Contributing

Contributions to improve the packaging are welcome! Please submit pull requests or issues on GitHub.
