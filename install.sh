#!/bin/sh

apt-get update
apt-get upgrade -y
apt-get install python3-pip -y
apt-get install ttf-dejavu -y
apt-get install python3-pil -y
apt-get install npm -y
npm install pm2 -g
pip3 install adafruit-circuitpython-pcd8544
pip3 install psutil
pip3 install gpiozero
pm2 start main.py --interpreter python3
pm2 save
pm2 startup