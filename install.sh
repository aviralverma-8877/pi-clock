#!/bin/sh

apt-get update
apt-get upgrade -y
apt-get install python3-pip -y
apt-get install ttf-dejavu
apt-get install python3-pil
apt-get install python3-pil
pip3 install adafruit-circuitpython-pcd8544
pip3 install psutil
pip3 install gpiozero