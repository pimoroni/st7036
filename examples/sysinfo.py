import datetime
import fcntl
import math
import socket
import struct
import threading
import time
from sys import exit

try:
    import psutil
except ImportError:
    exit("This script requires the psutil module\nInstall with: sudo pip install psutil")

import dogbl
import doglcd


def get_ip_address(ifname):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(),
                                        0x8915, # SIOCGIFADDR
                                        struct.pack('256s', ifname[:15])
                                    )[20:24])
    except IOError:
        return ifname + ' not found!'

lcd = doglcd.DogLCD(10,11,25,8,-1,-1)

lcd.begin(doglcd.DOG_LCD_M163, 0x28)
lcd.clear()
lcd.home()
lcd.noCursor()
lcd.noDoubleHeight()
lcd.noAutoscroll()

bl = dogbl.DogBL(1)
bl.RGB(100,0,50)
bl.update()

class StoppableThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        self.daemon = True

    def start(self):
        if not self.isAlive():
            self.stop_event.clear()
            threading.Thread.start(self)


    def stop(self):
        if self.isAlive():
            self.stop_event.set()
            self.join()


class AsyncWorker(StoppableThread):
    def __init__(self, fn):
        StoppableThread.__init__(self)
        self.fn = fn
        self.iterations = 0

    def run(self):
        while not self.stop_event.is_set():
            if not self.fn(self.iterations):
                break
            self.iterations += 1

def dosweep(i):
    hue = i%360
    bl.sweep(hue,20)
    time.sleep(0.05)
    return True

blfade = AsyncWorker(dosweep)

try:
    blfade.start()
except KeyboardInterrupt:
    blfade.stop()
    raise

DOG_LCD_CHEVRON_L = 0b11111011
DOG_LCD_CHEVRON_R = 0b11111100

# We need some custom characters to
# complete the levels of bar graph
lcd.createChar(6,[0,31,0,0,0,0,0,0])
lcd.createChar(5,[0,0,31,0,0,0,0,0])
lcd.createChar(4,[0,0,0,0,31,0,0,0])
lcd.createChar(3,[0,0,0,0,0,31,0,0])
lcd.createChar(2,[0,0,0,0,0,0,0,31])

# Always call home after creating
# custom chars
lcd.home()

# Map out the levels of bar graph
graph_steps = [2,95,3,4,45,5,6,255]

graph_text = []

while 1:
    #lcd.setCursor(0,0)
    #lcd.write(get_ip_address('eth0'))

    #lcd.setCursor(0,1)
    #lcd.write(get_ip_address('wlan0'))

    ip = psutil.net_connections(kind='inet4')
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent()

    lcd.setCursor(0,0)
    lcd.write("FREE " + str(mem.available/1024/1024) + 'MB/' + str(mem.total/1024/1024) + 'MB')

    lcd.setCursor(0,1)
    lcd.write("CPU% " + str(round(cpu,2)) + '    ')

    idx = int(math.floor((7.0/100.0) * cpu))

    graph_text.append(graph_steps[idx])

    if len(graph_text) > 16:
        graph_text.pop(0)

    lcd.setCursor(0,2)
    for char in graph_text:
        lcd.writeChar(char)

    time.sleep(0.25)
