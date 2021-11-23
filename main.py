# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time
from datetime import datetime
import psutil

import adafruit_pcd8544
import board
import busio
import digitalio

from gpiozero import LED
from gpiozero import Button
import math
import socket
from PIL import Image, ImageDraw, ImageFont
from subprocess import PIPE, Popen
import os
import fcntl
import struct
from functions.funct import function

spi = busio.SPI(board.SCK, MOSI=board.MOSI)
dc = digitalio.DigitalInOut(board.D23) # data/command
cs = digitalio.DigitalInOut(board.CE0) # Chip select
reset = digitalio.DigitalInOut(board.D24) # reset
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output()
backlight.value = False

# Hardware SPI usage:
display = adafruit_pcd8544.PCD8544(spi, dc, cs, reset)
# Software SPI usage (defaults to bit-bang SPI interface):
#disp = LCD.PCD8544(DC, RST, SCLK, DIN, CS)
# Initialize library.
display.bias = 5
display.contrast = 50
display.fill(0)
display.show()

# Button Def
prev_btn = digitalio.DigitalInOut(board.D27)
next_btn = digitalio.DigitalInOut(board.D18)
yes_btn = digitalio.DigitalInOut(board.D17)
no_btn = digitalio.DigitalInOut(board.D25)

prev_btn.switch_to_input()
next_btn.switch_to_input()
yes_btn.switch_to_input()
no_btn.switch_to_input()

menu = ["       Time        ", "       Date        ","    Network      "," Temperature      ","        CPU      ","        RAM      ","       DISK     ","    Back LED    ","    Contrast    ","      Volume    ","    Shutdown      ", "    Restart      "]
img = ["time.bmp", "calendar.bmp","network.bmp","temperature.bmp","cpu.bmp","ram.bmp","disk.bmp","bkled.bmp","contrast.bmp","volume.bmp","shutdown.bmp","restart.bmp"]
func_list = ["functions.get_time","functions.get_date","functions.get_ip","functions.get_cpu_temperature","functions.get_cpu","functions.get_ram","functions.get_disk","functions.toggleBkled","functions.set_contrast","functions.set_volume","functions.shutdown","functions.restart"]

head = None
body = None
msg = None
option = 0
btn_pressed = False
command = "no"
count = 0
functions = function(prev_btn,next_btn,yes_btn,no_btn, led, disp, contr)

while(True):
    mem = psutil.virtual_memory()
    if not btn_pressed:
        btn_pressed = True
        if not next_btn.value:
            command = ""
            option = option + 1
            if option == len(menu):
                option = 0
        elif not prev_btn.value:
            command = ""
            option = option - 1
            if option == -1:
                option = int(len(menu)-1)
        if not yes_btn.value:
            command = "yes"
        elif not no_btn.value:
            command = "no"
        else:
            command = ""
    if functions.no_button_pressed():
        btn_pressed = False
    msg, body = eval(str(func_list[option])+"(\""+str(command)+"\")")
    head = menu[option]
    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.open('images/'+img[option]).resize((LCD.LCDWIDTH, LCD.LCDHEIGHT), Image.ANTIALIAS).convert('1')
    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)
    # Load default font.
    #font = ImageFont.load_default()
    # Alternatively load a TTF font.
    # Some nice fonts to try: http://www.dafont.com/bitmap.php
    font = ImageFont.truetype('fonts/EnterCommand.ttf', 15)
    # Write some text.
    draw.text((0,1), head, font=font)
    draw.text((0,36), body, font=font)
    draw.text((25,13), msg, font=font)
    # Display image.
    if count == 5:
        disp.image(image)
        display.show()
        count = 0
    count = count + 1
    time.sleep(0.05)
