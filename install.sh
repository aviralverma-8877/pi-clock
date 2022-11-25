#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

cd ~
apt update -y
apt autoremove -y
apt update --fix-missing -y
apt install git python3-pip python3-pil -y
pip3 install adafruit-circuitpython-pcd8544
pip3 install psutil
pip3 install gpiozero
sudo raspi-config nonint do_spi 0
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock
cp pi_clock.service /etc/systemd/system/
chmod 777 /etc/systemd/system/pi_clock.service
sudo systemctl daemon-reload
sudo systemctl start pi_clock.service
sudo systemctl enable pi_clock.service