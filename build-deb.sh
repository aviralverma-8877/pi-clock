#!/bin/bash
# Script to build pi-clock Debian package for Raspberry Pi

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Package information
PACKAGE_NAME="pi-clock"
VERSION="2.0.0"
ARCH="all"
BUILD_DIR="debian"
PACKAGE_DIR="${BUILD_DIR}/opt/${PACKAGE_NAME}"

echo -e "${GREEN}Building ${PACKAGE_NAME} v${VERSION} for ${ARCH}${NC}"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "main" ] || [ ! -d "functions" ]; then
    echo -e "${RED}Error: This script must be run from the pi-clock root directory${NC}"
    exit 1
fi

# Clean previous build
echo -e "${YELLOW}Cleaning previous build...${NC}"
if [ -d "${BUILD_DIR}/opt" ]; then
    rm -rf "${BUILD_DIR}/opt"
fi
if [ -f "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" ]; then
    rm -f "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
fi

# Create package directory structure
echo -e "${YELLOW}Creating package directory structure...${NC}"
mkdir -p "${PACKAGE_DIR}"
mkdir -p "${BUILD_DIR}/DEBIAN"

# Copy application files
echo -e "${YELLOW}Copying application files...${NC}"
cp -r functions "${PACKAGE_DIR}/"
cp -r images "${PACKAGE_DIR}/"
cp -r fonts "${PACKAGE_DIR}/"
cp main "${PACKAGE_DIR}/"
cp pi_clock.service "${PACKAGE_DIR}/"
cp README.md "${PACKAGE_DIR}/"

# Copy DEBIAN control files if they don't exist
if [ ! -f "${BUILD_DIR}/DEBIAN/control" ]; then
    echo -e "${RED}Error: DEBIAN/control file not found${NC}"
    echo "Please create debian/DEBIAN/control first"
    exit 1
fi

# Set proper permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chmod 755 "${PACKAGE_DIR}/main"
chmod 644 "${PACKAGE_DIR}/pi_clock.service"
chmod -R 755 "${BUILD_DIR}/DEBIAN"
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"
chmod 755 "${BUILD_DIR}/DEBIAN/prerm"
chmod 755 "${BUILD_DIR}/DEBIAN/postrm"

# Update systemd service file for package installation
echo -e "${YELLOW}Updating systemd service file...${NC}"
cat > "${PACKAGE_DIR}/pi_clock.service" << 'EOF'
[Unit]
Description=Nokia 5110 LCD based clock and system monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/pi-clock/
ExecStart=/usr/bin/python3 /opt/pi-clock/main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create .gitignore in package directory to avoid including it
echo "*" > "${PACKAGE_DIR}/.gitignore"

# Calculate installed size (in KB)
INSTALLED_SIZE=$(du -sk "${BUILD_DIR}/opt" | cut -f1)
echo "Installed-Size: ${INSTALLED_SIZE}" >> "${BUILD_DIR}/DEBIAN/control"

# Build the package
echo -e "${YELLOW}Building Debian package...${NC}"
dpkg-deb --build "${BUILD_DIR}" "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

# Check if package was created successfully
if [ -f "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" ]; then
    PACKAGE_SIZE=$(du -h "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb" | cut -f1)
    echo ""
    echo -e "${GREEN}✓ Package built successfully!${NC}"
    echo "=================================================="
    echo "Package: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    echo "Size: ${PACKAGE_SIZE}"
    echo ""
    echo "To install on Raspberry Pi:"
    echo "  sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
    echo "  sudo apt-get install -f  # Install dependencies if needed"
    echo ""
    echo "To remove:"
    echo "  sudo dpkg -r ${PACKAGE_NAME}"
    echo ""
    echo "To purge (remove with config):"
    echo "  sudo dpkg -P ${PACKAGE_NAME}"
    echo ""
    echo "Package information:"
    dpkg-deb --info "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
else
    echo -e "${RED}✗ Package build failed!${NC}"
    exit 1
fi
