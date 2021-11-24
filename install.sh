#!/bin/sh

apt update -y
apt autoremove -y
apt update --fix-missing -y
apt install git python3-pip python3-pil -y
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock
pip3 install adafruit-circuitpython-pcd8544
pip3 install psutil
pip3 install gpiozero
crontab -l > crontab_new 
echo "@reboot cd $PWD && python3 main.py" > crontab_new
crontab crontab_new
rm crontab_new
reboot