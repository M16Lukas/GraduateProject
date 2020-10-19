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
import board
import neopixel

###############################
###          BH1750         ###
###############################

class Illuminance(threading.Thread):
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
	
	def __init__(self):
		threading.Thread.__init__(self)

	def readIlluminance(self):
		# Create I2C library
		i2c = smbus.SMBus(I2C_CH)
		# Read 2 bytes measured in the measurement mode 'CONT_H_RES_MODE'
		luxBytes - i2c.read_i2c_block_data(BH1750_DEV_ADDR, CONT_H_RES_MODE, 2)
		# 'bytes Array' to 'int'
		lux = int.from_bytes(luxBytes, byteorder='big')
		i2c.close()
		return lux
	
	def readIlluminanceThread(self):
		while True:
			print('{0} lux'.format(readIlluminance()))
			time.sleep(1)

################################
###         Neopixel         ###
################################

class Neopixel(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		pixels = neopixel.NeoPixel(board.D18, 8) # GPIO 18, 8 channal
	
	def runNeo(self):
		while True:
			pixels.fill((255,0,0)) # R : 255, G : 0, B : 0 = RED
			pixels.show()
	
	def stopNeo(self):
		pixels.sleep(1)


################################
###       Main Function      ###
################################

Illu = Illuminance()
Neo = Neopixel()

While True:
	lux_chk = Illu.readIlluminance()
	if lux_chk < 10:
		Neo.runNeo()
	else:
		Neo.stopNeo()
