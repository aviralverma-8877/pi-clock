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
pip3 install adafruit-circuitpython-pcd8544 --break-system-packages
pip3 install psutil --break-system-packages
pip3 install gpiozero --break-system-packages
pip3 install python-apt --break-system-packages
sudo raspi-config nonint do_spi 0
DIR="pi-clock"
if [ -d "$DIR" ]; then
   rm -r $DIR
fi
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock
chmod 777 pi_clock.service
FILE="/etc/systemd/system/pi_clock.service"
if [ -f "$FILE" ]; then
   rm $FILE
fi
ln -s $PWD/pi_clock.service /etc/systemd/system/pi_clock.service
sudo systemctl daemon-reload
sudo systemctl start pi_clock.service
sudo systemctl enable pi_clock.service
sudo rm install.sh