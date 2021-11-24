#!/bin/sh

apt update
apt autoremove
apt install git -y
git clone https://github.com/aviralverma-8877/pi-clock.git
cd pi-clock
apt install python3-pip -y
apt install ttf-dejavu -y
apt install python3-pil -y
apt install npm -y
npm install pm2 -g
pip3 install adafruit-circuitpython-pcd8544
pip3 install psutil
pip3 install gpiozero
pm2 start main.py --interpreter python3
pm2 save
pm2 startup