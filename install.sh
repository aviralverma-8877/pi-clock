#!/bin/sh

apt-get update
apt-get upgrade -y
apt-get install python3-pip -y
pip3 install adafruit-circuitpython-pcd8544
apt-get install ttf-dejavu
apt-get install python3-pil
pip3 install psutil
sudo apt-get install python3-pil
