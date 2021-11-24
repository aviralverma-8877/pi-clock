#!/bin/sh

apt update -y
apt autoremove -y
apt update --fix-missing -y
apt install git python3-pip ttf-dejavu python3-pil npm -y
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock
npm install pm2 -g
pip3 install adafruit-circuitpython-pcd8544
pip3 install psutil
pip3 install gpiozero
pm2 start main.py --interpreter python3
pm2 save
pm2 startup