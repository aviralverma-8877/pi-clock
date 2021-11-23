#!/bin/sh

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi
apt-get update
apt-get upgrade -y
apt-get install python3-pip -y
apt-get install ttf-dejavu
apt-get install python3-pil
apt-get install python3-pil
apt-get install npm -y
npm install pm2 -g
pip3 install adafruit-circuitpython-pcd8544
pip3 install psutil
pip3 install gpiozero
pm2 start main.py --interpreter python3
pm2 save
pm2 startup