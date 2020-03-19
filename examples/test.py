#!/usr/bin/env python

import datetime
import dogbl
import threading
import time

import doglcd


lcd = doglcd.DogLCD(10, 11, 25, 8, -1, -1)

lcd.begin(doglcd.DOG_LCD_M163, 0x28)

lcd.clear()
lcd.home()
lcd.write(chr(0) + 'OMG! Such time' + chr(0))
lcd.setCursor(0, 2)
lcd.write(chr(1) + chr(4) + ' Very Wow! ' + chr(3) + chr(2) + chr(5))

bl = dogbl.DogBL(1)
bl.RGB(100, 0, 50)
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
    hue = (i * 4) % 360
    bl.sweep(hue, 40)
    time.sleep(0.05)
    return True


blfade = AsyncWorker(dosweep)

try:
    blfade.start()
except KeyboardInterrupt:
    blfade.stop()
    raise

pirate = [
    [0x00, 0x1f, 0x0b, 0x03, 0x00, 0x04, 0x11, 0x1f],
    [0x00, 0x1f, 0x16, 0x06, 0x00, 0x08, 0x03, 0x1e],
    [0x00, 0x1f, 0x0b, 0x03, 0x00, 0x04, 0x11, 0x1f],
    [0x00, 0x1f, 0x05, 0x01, 0x00, 0x02, 0x08, 0x07]
]

heart = [
    [0x00, 0x0a, 0x1f, 0x1f, 0x1f, 0x0e, 0x04, 0x00],
    [0x00, 0x00, 0x0a, 0x0e, 0x0e, 0x04, 0x00, 0x00],
    [0x00, 0x00, 0x00, 0x0e, 0x04, 0x00, 0x00, 0x00],
    [0x00, 0x00, 0x0a, 0x0e, 0x0e, 0x04, 0x00, 0x00]
]

raa = [
    [0x1f, 0x1d, 0x19, 0x13, 0x17, 0x1d, 0x19, 0x1f],
    [0x1f, 0x17, 0x1d, 0x19, 0x13, 0x17, 0x1d, 0x1f],
    [0x1f, 0x13, 0x17, 0x1d, 0x19, 0x13, 0x17, 0x1f],
    [0x1f, 0x19, 0x13, 0x17, 0x1d, 0x19, 0x13, 0x1f]
]

arr = [
    [31, 14, 4, 0, 0, 0, 0, 0],
    [0, 31, 14, 4, 0, 0, 0, 0],
    [0, 0, 31, 14, 4, 0, 0, 0],
    [0, 0, 0, 31, 14, 4, 0, 0],
    [0, 0, 0, 0, 31, 14, 4, 0],
    [0, 0, 0, 0, 0, 31, 14, 4],
    [4, 0, 0, 0, 0, 0, 31, 14],
    [14, 4, 0, 0, 0, 0, 0, 31]
]

char = [
    [12, 11, 9, 9, 25, 25, 3, 3],
    [0, 15, 9, 9, 9, 25, 27, 3],
    [3, 13, 9, 9, 9, 27, 27, 0],
    [0, 15, 9, 9, 9, 25, 27, 3]
]

pacman = [
    [0x0e, 0x1f, 0x1d, 0x1f, 0x18, 0x1f, 0x1f, 0x0e],
    [0x0e, 0x1d, 0x1e, 0x1c, 0x18, 0x1c, 0x1e, 0x0f]
]


def getAnimFrame(char, fps):
    return char[int(round(time.time() * fps) % len(char))]


while 1:
    lcd.createChar(0, getAnimFrame(char, 4))
    lcd.createChar(1, getAnimFrame(arr, 16))
    lcd.createChar(2, getAnimFrame(raa, 8))
    lcd.createChar(3, getAnimFrame(pirate, 2))
    lcd.createChar(4, getAnimFrame(heart, 4))
    lcd.createChar(5, getAnimFrame(pacman, 3))
    lcd.setCursor(0, 1)
    t = datetime.datetime.now().strftime("%H:%M:%S.%f")
    lcd.write(t)
