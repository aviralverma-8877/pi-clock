import time
from datetime import datetime
import psutil
from gpiozero import LED
from gpiozero import Button
import Adafruit_Nokia_LCD as LCD
import Adafruit_GPIO.SPI as SPI
import math
import socket
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from subprocess import PIPE, Popen
import os
import fcntl
import struct

class function(object):
    def __init__(self, prev_btn, next_btn, yes_btn, no_btn):
        self.prev_btn = prev_btn
        self.next_btn = next_btn
        self.yes_btn = yes_btn
        self.no_btn = no_btn

    def get_ip_address(self, ifname):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
            )[20:24])
        except:
            return None

    def get_time(self,format):
        if format == "yes":
            return str(datetime.now().strftime("%H:%M:%S")), "24hr      am/pm"
        else:
            return str(datetime.now().strftime("%I:%M:%S %p")), "24hr      am/pm" 



    def get_date(self,format):
        return str(datetime.now().strftime("%d-%m-%Y\n%B")), str(datetime.now().strftime("%A"))

    def shutdown(self,comm):
        if comm == "yes":
            os.system("shutdown -h now")
            return "", "yes         Wait.."
        else:
            return "", "yes              "

    def restart(self,comm):
        if comm == "yes":
            os.system("reboot")
            return "", "yes         Wait.."
        else:
            return "", "yes              "

    def get_cpu(self,comm):
        cpu = str(psutil.cpu_freq().current)
        pert = str(psutil.cpu_percent()) 
        return cpu+" GHz\n", "Util "+pert+" %"

    def get_ram(self,comm):
        mem = psutil.virtual_memory()
        fram = str(round(float(mem.free)/(1024*1024),1))
        uram = str(round(float(mem.used)/(1024*1024),1))
        rem = str(round(float(mem.total)/(1024*1024),1))
        return " F "+fram+" MB\n U "+uram+" MB","RAM: "+rem+" MB"

    def get_cpu_temperature(self,comm):
        """get cpu temperature using vcgencmd"""
        process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
        output, _error = process.communicate()
        temp_c = int(float(output[output.index('=') + 1:output.rindex("'")]))
        temp_f = int((temp_c*9/5)+32)
        if comm == "no":
            return str(temp_c)+" C","C              F"
        if comm == "yes":
            return str(temp_f)+" F","C              F"


    def get_ip(self,comm):
        IPAddr = self.get_ip_address('eth0')
        con = "Connection:\nEthernet"
        if IPAddr == None:
            IPAddr = self.get_ip_address('wlan0')
            con = "Connection:\nWiFi"
            if IPAddr == None:
                IPAddr = "Not Connected"
                con = ""
        return con, IPAddr

    def no_button_pressed(self):
        if not self.next_btn.is_pressed:
            if not self.prev_btn.is_pressed:
                if not self.yes_btn.is_pressed:
                    if not self.no_btn.is_pressed:
                        return True
        return False