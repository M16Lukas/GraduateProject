#!/usr/bin/python
"""
- Title  : Bicycle Smart Lock
- Writer : Minho Park
- Date   : 10-25-2020 
"""

import sys
import os
import threading
import dbus
import dbus.mainloop.glib

# bh1750
import smbus

# neopixel
import neopixel
import board

from time import sleep, time
from bluez_components import *

import RPi.GPIO as GPIO
import numpy as np
import subprocess as sp

try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

 
mainloop = None

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

neo_pin = board.D18		# GPIO PIN
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

	def showNeo(self,RGB_list):
     R = RGB_list[0]
     G = RGB_list[1]
     B = RGB_list[2]
     
     pixels.fill((R,G,B))
     pixels.show()

	def controlNeopixelThread(self):
		   lux_chk = self.readIlluminance()
		   if lux_chk < 15:
			     self.showNeo([0,255,0])
		   else:
			     self.showNeo([0,0,0])
 
 
 def selectNeopixelColor(in_value):
    neo_clr = [[2,3],[3,4],[4,5],[5,6],[6,7],[7,8]]
    neo_rgb = {0:[255,0,0], 1:[255,94,0], 2:[255,228,0], 3:[0,255,0], 4:[0,0,255], 5:[217,65,197], 6:[0,0,0]}
    
    i = in_value[0]-2
    confirm_num = np.equal(neo_clr[i], in_value)
    
    if False in confirm_num:
        return neo_rgb[6]
    else:
        return neo_rgb[i]
 
 
################################
###     DC Motor Control     ###
################################
# Init
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# Pin
Rght = 36 # BCM(16), IN1, Rght
Lft  = 38 # BCM(20), IN2, Lft
ENB  = 40 # BCM(21), PWM
    
# GPIO
GPIO.setup(Rght, GPIO.OUT)
GPIO.setup(Lft, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
        
# PWM
pwm = GPIO.PWM(ENB, 100)
pwm.start(0)

# Lock Function
def Lock_Close():
    print("lock close")
    GPIO.output(Rght, GPIO.HIGH)
    GPIO.output(Lft, GPIO.LOW)
    GPIO.output(ENB, GPIO.HIGH)
    pwm.ChangeDutyCycle(40)
    sleep(5)
    stop()


def Lock_Open():
    print("lock open")
    GPIO.output(Rght, GPIO.LOW)
    GPIO.output(Lft, GPIO.HIGH)
    GPIO.output(ENB, GPIO.HIGH)
    pwm.ChangeDutyCycle(40)
    sleep(5)
    stop()


def stop():
    print("stopping motor")
    GPIO.output(Rght, GPIO.LOW)
    GPIO.output(Lft, GPIO.LOW)
    GPIO.output(ENB, GPIO.LOW)
    
    
# Confirm entered password
def check_password(values):
    list_value = []
    for v in values:
        list_value.append(int(v))

    Crypto_Open_Code  = [1, 15, 5, 13, 8, 11]
    Crypto_Close_Code = [15, 13, 7, 12, 4, 14]
    if values[0] == 1:
        ch = np.equal(Crypto_Open_Code, values)
        if False in ch:
            stop()
        else:
            Lock_Open()
            Illuminance().controlNeopixelThread()
            
    elif values[0] == 15:
        ch = np.equal(Crypto_Close_Code, values)
        if False in ch:
            stop()
        else:
            Lock_Close()
          
    ### NeoPixel
    elif values[0] >= 2 and values[0] <= 7:
        neo_color = selectNeopixelColor(values)
        Illuminance().showRGB(neo_color)
    else:
        stop()


class cmdChrc(Characteristic):
    CMD_UUID = '0d0f0fe1-0e65-1d70-855e-02505f9c40e1'
 
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CMD_UUID, 
            ['write'],
            service)
 
    def WriteValue(self, value, options):
        print('RowCharacteristic Write: ' + repr(value))
        check_password(value)
 
 
class MotorService(Service):
    SVC_UUID = '0d0f0fe1-0e65-1d70-855e-02505f9c40e0'
 
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.SVC_UUID, True)
        self.add_characteristic(cmdChrc(bus, 0, self))


#######################################
###      Function Registration      ###
#######################################
 
class Func_Application(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(MotorService(bus, 0))
 
 
class Func_Advertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_local_name('AutoBy')
        self.include_tx_power = True


def register_ad_cb():
    """
    Callback if registering advertisement was successful
    """
    print('Advertisement registered')
 
 
def register_ad_error_cb(error):
    """
    Callback if registering advertisement failed
    """
    print('Failed to register advertisement: ' + str(error))
    mainloop.quit()
 
 
def register_app_cb():
    """
    Callback if registering GATT application was successful
    """
    print('GATT application registered')
 
 
def register_app_error_cb(error):
    """
    Callback if registering GATT application failed.
    """
    print('Failed to register application: ' + str(error))
    mainloop.quit()
 
 
def main():
    global mainloop
 
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
 
    bus = dbus.SystemBus()
 
    # Get ServiceManager and AdvertisingManager
    service_manager = get_service_manager(bus)
    ad_manager = get_ad_manager(bus)
 
    # Create gatt services
    func_app = Func_Application(bus)
 
    # Create advertisement
    func_advertisement = Func_Advertisement(bus, 0)
    
    mainloop = GObject.MainLoop()
 
    # Register gatt services
    service_manager.RegisterApplication(func_app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
 
    # Register advertisement
    ad_manager.RegisterAdvertisement(func_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=register_ad_error_cb)
                                     
 
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("Finished")
        pwm.stop()
        GPIO.cleanup()
        os._exit(1)
    
    pwm.stop()
    GPIO.cleanup()
    os._exit(1)
 
 
if __name__ == '__main__':
    main()
