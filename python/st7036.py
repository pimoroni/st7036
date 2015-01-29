#!/usr/bin/env python

import spi, time
import RPi.GPIO as GPIO

COMMAND_CLEAR = 0x01
COMMAND_HOME = 0x02
COMMAND_SET_DISPLAY_MODE = 0b00001000

BLINK_ON = 0b00000001
CURSOR_ON  = 0b00000010
DISPLAY_ON = 0b00000100

class st7036():
    def __init__(self, register_select_pin, rows=3, columns=16, spi_chip_select=0, instruction_set_template=0b00111000):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.spi = spi.SPI("/dev/spidev0.{}".format(spi_chip_select))
        self.spi.speed = 1000000
        self.spi.bits_per_word = 8
        
        self.row_offsets = ([0x00], [0x00, 0x40], [0x00, 0x10, 0x20])[rows - 1]
        self.rows = rows
        self.columns = columns

        GPIO.setup(register_select_pin, GPIO.OUT)
        GPIO.output(register_select_pin, GPIO.HIGH)

        self.register_select_pin = register_select_pin
        self.instruction_set_template = instruction_set_template

        self.animations = []*8

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
        mask  = COMMAND_SET_DISPLAY_MODE
        mask |= DISPLAY_ON if enable == True else 0
        mask |= CURSOR_ON if cursor == True else 0
        mask |= BLINK_ON if blink == True else 0      
        self._write_command(mask)

    def set_cursor_offset(self, offset):
        """ 
        Sets the cursor position in DRAM

        Args:
            offset (int): DRAM offset to place cursor
        """            
        self._write_command(0b10000000 | offset)

    def set_cursor_position(self, column, row):
        """ 
        Sets the cursor position in DRAM based on
        a row and column offset

        Args:
            column (int): column to move the cursor to
            row (int): row to move the cursor to
       Raises:
            ValueError: if row and column are not within defined screen size
        """
        if row not in range(self.rows) or column not in range(self.columns):
            raise ValueError( "row and column must integers within the defined screen size")

        offset = self.row_offsets[row] + column

        self._write_command(0b10000000 | offset)

    def home(self):
        """
        Sets the cursor position to 0,0
        """
        self.set_cursor_position(0,0)

    def clear(self):
        """ 
        Clears the display and resets the cursor.
        """            
        self._write_command(COMMAND_CLEAR)
        self.home()

    def write(self, value):
        """ 
        Write a string to the current cursor position.

        Args:
            value (string): The string to write
        """
        GPIO.output(self.register_select_pin, GPIO.HIGH)

        for i in [ord(char) for char in value]:
            self.spi.write([i])
            time.sleep(0.00005)
        
    def create_animation(self, anim_pos, anim_map, frame_rate):
        self.create_char(anim_pos, anim_map[0])
        self.animations[anim_pos] = [anim_map,frame_rate]
        self.set_cursor_position(0,1)

    def update_animations(self):
        for i,animation in enumerate(self.animations):
            if len(animation) == 2:
                anim = animation[0]
                fps = animation[1]
                frame = anim[ int(round(time.time()*fps) % len(anim)) ]
                self.create_char(i,frame)
        self.set_cursor_position(0,1)

    def create_char(self, char_pos, char_map):
        if(char_pos<0 or char_pos>7):
            return False

        baseAddress = char_pos*8
        for i in range(0,8):
            self._write_command((0x40|(baseAddress+i)))
            self._write_char(char_map[i])

        self.set_display_mode()

    def _write_char(self, value):
        GPIO.output(self.register_select_pin, GPIO.HIGH)
        self.spi.write([value])

        time.sleep(0.0001) #0.00005

    def _write_command(self, value, instruction_set=0):
        GPIO.output(self.register_select_pin, GPIO.LOW)

        # select correct instruction set
        self.spi.write([self.instruction_set_template | instruction_set])

        time.sleep(0.00005)

        # switch to command-mode
        self.spi.write([value])

        time.sleep(0.00005)

if __name__ == "__main__":
    print("st7036 test cycles")
    
    import time, sys, os, math, random

    # disable output buffering for our test activity dots
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    lcd = st7036(register_select_pin=25, rows=3, columns=16)
    lcd.set_display_mode()
    lcd.set_contrast(40)
    lcd.clear()

    print(">> fill screen")
    for i in range(48):
        lcd.set_cursor_offset(i)
        time.sleep(.05)
        lcd.write(chr(i+65))
        time.sleep(.02)        

    print(">> cycle character set")
    for i in range(256 - 48 - 65):
        lcd.set_cursor_offset(0x00)
        lcd.write("".join([chr(i + j + 65) for j in range(48)]))
        time.sleep(.02)
        lcd.clear()
    lcd.clear()

    print(">> test contrast range")
    lcd.set_cursor_offset(0x10)
    lcd.write("test contrast")
    for i in range(0x40):                
        lcd.set_contrast(i)
        time.sleep(0.02)
    for i in reversed(range(0x40)):                
        lcd.set_contrast(i)
        time.sleep(0.02)
    lcd.set_contrast(40)
    lcd.clear()

    print(">> test set cursor position")
    for i in range(50):
        row = random.randint(0, 3 - 1)
        column = random.randint(0, 16 - 1)
        print("Row:{} Column:{}".format(row, column))
        lcd.set_cursor_position(column, row)
        lcd.write(chr(0b01101111))
        time.sleep(.10)  
        lcd.set_cursor_position(column, row)
        lcd.write(" ")
    








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
