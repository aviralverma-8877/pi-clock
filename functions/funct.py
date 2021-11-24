from datetime import datetime
import psutil
from gpiozero import CPUTemperature
import socket
from subprocess import PIPE, Popen
import os
import fcntl
import struct

class function(object):
    def __init__(self, prev_btn, next_btn, yes_btn, no_btn, bkled, disp, contrast):
        self.prev_btn = prev_btn
        self.next_btn = next_btn
        self.yes_btn = yes_btn
        self.no_btn = no_btn
        self.bkled = bkled
        self.disp = disp
        self.contrast = contrast
        self.last_comm = "yes"

    def toggleBkled(self, comm):
        if comm == "no":
            self.bkled.value = True
            return "  ON","OFF           ON"
        elif comm == "yes":
            self.bkled.value = False
            return "  OFF","OFF           ON"
        else:
            if self.bkled.value:
                return "  ON","OFF           ON"
            else:
                return "  OFF","OFF           ON"
                
    def get_disk(self, comm):
        disk = psutil.disk_usage('/')
        free = str(round(float(disk.free)/(1024*1024*1024),1))
        total = str(round(float(disk.total)/(1024*1024*1024),1))
        return "Free "+free+" GB","Total "+total+" GB"
    
    def get_time(self,comm):
        if comm == "yes":
            self.last_comm = comm
            return str(datetime.now().strftime("%H:%M:%S")), "24hr      am/pm"
        elif comm == "no":
            self.last_comm = comm
            return str(datetime.now().strftime("%I:%M:%S %p")), "24hr      am/pm" 
        else:
            if self.last_comm == "yes":
                return str(datetime.now().strftime("%H:%M:%S")), "24hr      am/pm"
            else:
                return str(datetime.now().strftime("%I:%M:%S %p")), "24hr      am/pm" 

    def get_date(self,format):
        return str(datetime.now().strftime("%d-%m-%Y\n %B")), str(datetime.now().strftime("%A"))

    def set_volume(self, comm):
        if comm == "yes":
            os.system("alias volu='sudo amixer set PCM -- $[$(amixer get PCM|grep -o [0-9]*%|sed 's/%//')+5]%'")
        elif comm == "no":
            os.system("alias vold='sudo amixer set PCM -- $[$(amixer get PCM|grep -o [0-9]*%|sed 's/%//')-5]%'")
        return "","+              -" 

    def shutdown(self,comm):
        if comm == "yes":
            self.last_comm = "shutdown"
            os.system("shutdown -h now")
            return "", "yes         Wait.."
        else:
            if self.last_comm == "shutdown":
                return "", "yes         Wait.."
            else:
                return "", "yes              "

    def restart(self,comm):
        if comm == "yes":
            self.last_comm = "rebooting"
            os.system("reboot")
            return "", "yes         Wait.."
        else:
            if self.last_comm == "rebooting":
                return "", "yes         Wait.."
            else:
                return "", "yes              "
    def set_contrast(self,comm):
        if comm == "yes":
            if self.contrast > 40:
                self.contrast = self.contrast - 1
                self.disp.contrast = self.contrast
                self.disp.invert = True
        if comm == "no":
            if self.contrast < 70:
                self.contrast = self.contrast + 1
                self.disp.contrast = self.contrast
                self.disp.invert = True
        return "","+              -"       
    def get_cpu(self,comm):
        cpu = str(psutil.cpu_freq().current)
        pert = str(psutil.cpu_percent()) 
        return cpu+" MHz\n", "Util "+pert+" %"

    def get_ram(self,comm):
        mem = psutil.virtual_memory()
        fram = str(round(float(mem.free)/(1024*1024),1))
        uram = str(round(float(mem.used)/(1024*1024),1))
        rem = str(round(float(mem.total)/(1024*1024),1))
        return " F "+fram+" MB\n U "+uram+" MB","RAM: "+rem+" MB"

    def get_cpu_temperature(self,comm):
        """get cpu temperature using vcgencmd"""
        cpu = CPUTemperature()
        temp_c = float(cpu.temperature)
        temp_f = float((temp_c*9/5)+32)
        if comm == "yes":
            self.last_comm = comm
            return str(temp_f)+" F","F              C"
        elif comm == "no":
            self.last_comm = comm
            return str(temp_c)+" C","F              C"
        else:
            if self.last_comm == "yes":
                return str(temp_f)+" F","F              C"
            elif self.last_comm == "no":
                return str(temp_c)+" C","F              C"

    def get_ip(self,comm):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            IPAddr = s.getsockname()[0]
            con = "Local IP"
            s.close()
        except:
            con = "Link Down"
            IPAddr = "Not Available"
        return con, IPAddr

    def no_button_pressed(self):
        if self.next_btn.value:
            if self.prev_btn.value:
                if self.yes_btn.value:
                    if self.no_btn.value:
                        return True
        return False