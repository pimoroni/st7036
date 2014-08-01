#!/usr/bin/env python

import spidev, time
import RPi.GPIO as GPIO

COMMAND_CLEAR = 0x01
COMMAND_HOME = 0x02
COMMAND_SET_DISPLAY_MODE = 0x80

BLINK_ON = 0x01
CURSOR_ON  = 0x02
DISPLAY_ON = 0x04

class st7036():
    def __init__(self, register_select_pin, rows=3, cols=16, spi_chip_select=0, instruction_set_template=0b00111000):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.spi = spidev.SpiDev()
        self.spi.open(0, spi_chip_select)
        self.spi.max_speed_hz = 1000000

        self.line_offsets = ([0x00], [0x00, 0x40], [0x00, 0x10, 0x20])[rows - 1]
        self.rows = rows
        self.cols = cols

        GPIO.setup(register_select_pin, GPIO.OUT)
        GPIO.output(register_select_pin, GPIO.HIGH)

        self.register_select_pin = register_select_pin
        self.instruction_set_template = instruction_set_template

        self.set_display_mode()

        # set entry mode (no shift, cursor direction)        
        self._write_command(0b00000100 | 0b00000010)

        # ???
        self._write_command(0x1D, 1)

        self.set_contrast(40)
        self.clear()

    def set_contrast(self, contrast):
        """ 
        Sets the display contrast.

        Args:
            contrast (int): contrast value
        Raises:
            TypeError: if contrast is not an int
            ValueError: if contrast is not in the range 0..0x3F
        """            
        if type(contrast) is not int:
            raise TypeError( "contrast must be an integer")

        if contrast not in range(0, 0x40):
            raise ValueError( "contrast must be an integer in the range 0..0x3F")

        # For 3.3v operation the booster must be on, which is
        # on the same command as the (2-bit) high-nibble of contrast
        self._write_command((0b01010100 | ((contrast >> 4) & 0x03)), 1)
        self._write_command(0b01101011, 1)

        # Set low-nibble of the contrast
        self._write_command((0b01110000 | (contrast & 0x0F)), 1)

    def set_display_mode(self, enable=True, cursor=False, blink=False):
        """ 
        Sets the display mode.

        Args:
            enable (boolean): enable display output
            cursor (boolean): show cursor
            blink (boolean): blink cursor (if shown)
        """            
        mask  = DISPLAY_ON if enable == True else 0
        mask |= CURSOR_ON if cursor == True else 0
        mask |= BLINK_ON if blink == True else 0      
        #self._write_command(COMMAND_SET_DISPLAY_MODE | mask)
        self._write_command(0x08 | 0x04 | 0x02 | 0x01)

    def set_cursor_position(self, offset):
        """ 
        Sets the cursor position in DRAM

        Args:
            offset (int): DRAM offset to place cursor
        """            
        self._write_command(0b10000000 | offset)

    def clear(self):
        """ 
        Clears the display and resets the cursor.
        """            
        self._write_command(COMMAND_CLEAR)

    def write(self, value):
        """ 
        Write a string to the current cursor position.

        Args:
            value (string): The string to write
        """            
        GPIO.output(self.register_select_pin, GPIO.HIGH)

        for i in [ord(char) for char in value]:
            self.spi.xfer([i])
        

    def _write_command(self, value, instruction_set=0):
        GPIO.output(self.register_select_pin, GPIO.LOW)

        # select correct instruction set
        self.spi.xfer([self.instruction_set_template | instruction_set])

        time.sleep(0.00001)

        # switch to command-mode
        self.spi.xfer([value])

        time.sleep(0.00001)

if __name__ == "__main__":
    print "st7036 test cycles"
    
    import time, sys, os, math

    # disable output buffering for our test activity dots
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    lcd = st7036(register_select_pin=25)
    lcd.set_display_mode()
    lcd.set_contrast(40)
    lcd.clear()

    # for i in range(48):
    #     lcd.set_cursor_position(i)
    #     time.sleep(.1)
    #     lcd.write(chr(i+65))
    #     time.sleep(.1)



    print ">> fill screen"
    lcd.set_cursor_position(0x00)
    lcd.write("a" * 48)
    time.sleep(2)
    lcd.clear()

    print ">> cycle character set"
    for i in range(256 - 48):
        lcd.set_cursor_position(0x00)
        lcd.write("".join([chr(i + j) for j in range(48)]))
        time.sleep(.1)
        lcd.clear()

    print ">> test contrast range"
    lcd.set_cursor_position(0x10)
    lcd.write("test contrast")
    for i in range(0x40):                
        lcd.set_contrast(i)
        time.sleep(0.025)
    lcd.clear()

    lcd.set_contrast(40)








# UNPORTED METHODS

# def scrollDisplayLeft(self):
#     self.setInstructionSet(0)
#     self.writeCommand(DOG_LCD_SCROLL_LEFT,30) # 0x18

# def scrollDisplayRight(self):
#     self.setInstructionSet(0)
#     self.writeCommand(DOG_LCD_SCROLL_RIGHT,30) # 0x1C

# def leftToRight(self):
#     self.entryMode|=0x02
#     self.writeCommand(self.entryMode,30)

# def rightToLeft(self):
#     self.entryMode&=~0x02
#     self.writeCommand(self.entryMode,30)

# def autoScroll(self):
#     self.entryMode|=0x01
#     self.writeCommand(self.entryMode,30)

# def noAutoscroll(self):
#     self.entryMode&=~0x01
#     self.writeCommand(self.entryMode,30)

# def doubleHeight(self):
#     self.writeCommand(0b00100110,30)

# def noDoubleHeight(self):
#     self.writeCommand(0b00100001,30)

# def doubleHeightTop(self):
#     self.writeCommand(0b00011000,30)

# def doubleHeightBottom(self):
#     self.writeCommand(0b00010000,30)

# def createAnimation(self, anim_pos, anim_map, frame_rate):
#     self.createChar(anim_pos, anim_map[0])
#     self.animations[anim_pos] = [anim_map,frame_rate]
#     self.setCursor(0,1)

# def updateAnimations(self):
#     for i,animation in enumerate(self.animations):
#         if len(animation) == 2:
#             anim = animation[0]
#             fps = animation[1]
#             frame = anim[ int(round(time.time()*fps) % len(anim)) ]
#             self.createChar(i,frame)
#     self.setCursor(0,1)

# def createChar(self, char_pos, char_map):
#     if(char_pos<0 or char_pos>7):
#         return False

#     baseAddress = char_pos*8
#     self.setInstructionSet(0)
#     for i in range(0,8):
#         self.writeCommand((0x40|(baseAddress+i)),30)
#         self.writeChar(char_map[i])
#     self.setInstructionSet(0)
#     self.writeDisplayMode()

