.PHONY: help build install uninstall clean test

PACKAGE_NAME=pi-clock
VERSION=2.0.0
ARCH=armhf
DEB_FILE=$(PACKAGE_NAME)_$(VERSION)_$(ARCH).deb

help:
	@echo "Pi-Clock Debian Package Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make build      - Build the Debian package"
	@echo "  make install    - Install the built package"
	@echo "  make uninstall  - Uninstall the package"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make test       - Test the installation"
	@echo "  make info       - Show package information"
	@echo ""

build:
	@echo "Building Debian package..."
	./build-deb.sh

install: build
	@echo "Installing $(DEB_FILE)..."
	sudo dpkg -i $(DEB_FILE)
	@echo "Installing missing dependencies..."
	sudo apt-get install -f -y

uninstall:
	@echo "Uninstalling $(PACKAGE_NAME)..."
	sudo dpkg -r $(PACKAGE_NAME)

purge:
	@echo "Purging $(PACKAGE_NAME)..."
	sudo dpkg -P $(PACKAGE_NAME)

clean:
	@echo "Cleaning build artifacts..."
	rm -rf debian/opt/
	rm -f $(DEB_FILE)
	@echo "Clean complete."

test:
	@echo "Testing installation..."
	@sudo systemctl status pi_clock.service || true
	@echo ""
	@echo "View logs with:"
	@echo "  journalctl -u pi_clock.service -f"

info:
	@if [ -f "$(DEB_FILE)" ]; then \
		echo "Package information:"; \
		dpkg-deb --info $(DEB_FILE); \
		echo ""; \
		echo "Package contents:"; \
		dpkg-deb --contents $(DEB_FILE); \
	else \
		echo "Package not built yet. Run 'make build' first."; \
	fi

logs:
	@echo "Viewing service logs (Ctrl+C to exit)..."
	journalctl -u pi_clock.service -f

status:
	@sudo systemctl status pi_clock.service

restart:
	@echo "Restarting service..."
	@sudo systemctl restart pi_clock.service
	@echo "Service restarted."

stop:
	@echo "Stopping service..."
	@sudo systemctl stop pi_clock.service
	@echo "Service stopped."

start:
	@echo "Starting service..."
	@sudo systemctl start pi_clock.service
	@echo "Service started."
