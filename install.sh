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
touch /var/spool/cron/job
echo "@reboot cd $PWD && python3 main.py" > /var/spool/cron/job
chmod 600 /var/spool/cron/job
reboot