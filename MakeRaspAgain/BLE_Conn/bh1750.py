#!/usr/bin/python
"""
- Title  : Control Of Light Intensity Sensor(bh1750) and neopixel 
- Writer : Minho Park
- Date   : 10-20-2020 
"""

import threading
import time

# bh1750
import smbus

# neopixel
import neopixel
import board
import RPi.GPIO as GPIO

###############################
###          BH1750         ###
###############################
# i2c channal number
I2C_CH = 1

# BH1750 addr
BH1750_DEV_ADDR = 0x23

CONT_H_RES_MODE = 0x10
CONT_H_RES_MODE2 = 0x11
CONT_L_RES_MODE = 0x13
ONETIME_H_RES_MODE = 0x20
ONETIME_H_RES_MODE2 = 0x21
ONETIME_L_RES_MODE = 0x23

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

neo_pin = 12		# GPIO PIN
GPIO.setup(neo_pin, GPIO.OUT)

neo_cnt = 8				# Number of LED pixels 
neo_brightness = 0.2	# LED brightness

pixels = neopixel.NeoPixel(neo_pin, neo_cnt, brightness = neo_brightness)

class Illuminance(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

	def readIlluminance(self):
		# Create I2C library
		i2c = smbus.SMBus(I2C_CH)
		# Read 2 bytes measured in the measurement mode 'CONT_H_RES_MODE'
		luxBytes = i2c.read_i2c_block_data(BH1750_DEV_ADDR, CONT_H_RES_MODE, 2)
		# 'bytes Array' to 'int'
		lux = int.from_bytes(luxBytes, byteorder='big')
		i2c.close()
		return lux
	
	def controlNeopixelThread(self):
		while True:
			lux_chk = self.readIlluminance()
			print(lux_chk)
			if lux_chk < 20:
				pixels.fill((0,255,0)) # Green
				pixels.show()
			else:
				pixels.fill((0,0,0)) # Off
				pixels.show()
			time.sleep(3)


Illuminance().controlNeopixelThread()
