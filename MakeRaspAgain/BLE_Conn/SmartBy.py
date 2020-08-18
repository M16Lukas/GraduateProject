#!/usr/bin/python
"""
- Title  : Bicycle Smart Lock
- Writer : Minho Park
- Date   : 17-07-2020 
"""

import sys
import os
import threading
import dbus
import dbus.mainloop.glib

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

################################
###     DC Motor Control     ###
################################
# Init
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# Pin
Rght = 16 # BCM(23), IN1, Rght
Lft  = 18 # BCM(24), IN2, Lft
ENA  = 22 # BCM(25), PWM
    
# GPIO
GPIO.setup(Rght, GPIO.OUT)
GPIO.setup(Lft, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
        
# PWM
pwm = GPIO.PWM(ENA, 100)
pwm.start(0)

# Lock Function
def Lock_ON():
    print("lock on")
    GPIO.output(Rght, GPIO.HIGH)
    GPIO.output(ENA, GPIO.HIGH)
    for sp in range(15,26,2):
        pwm.ChangeDutyCycle(sp)
        sleep(0.2)
    stop()


def Lock_OFF():
    print("lock off")
    GPIO.output(Lft, GPIO.HIGH)
    GPIO.output(ENA, GPIO.HIGH)
    for sp in range(15,26,2):
        pwm.ChangeDutyCycle(sp)
        sleep(0.2)
    stop()


def stop():
    print("stopping motor")
    GPIO.output(Rght, GPIO.LOW)
    GPIO.output(Lft, GPIO.LOW)
    GPIO.output(ENA, GPIO.LOW)
    

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
            Lock_ON()
            
    elif values[0] == 15:
        ch = np.equal(Crypto_Close_Code, values)
        if False in ch:
            stop()
        else:
            Lock_OFF()
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
###       Black Box Control         ###
#######################################

class VideoChrc(Characteristic):
    CMD_UUID = '020a0df4-0c74-1a40-725e-01806fac4081'
    
    savepath = '/home/pi/MakeRaspAgain/VideoRecord'
    
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CMD_UUID, 
            ['read'],
            service)
        self.values = self.videoFile(self.savepath)
        
    def videoFile(self, path):
        files_list = os.listdir(path)
        
        video_list = []
        int_video_list = []
        
        for files in files_list:
            files = files.replace('-','')
            files = files.replace(':','')
            files = files.replace(' ','')
            files = files[:12]              # remove '.h264'
            video_list.append(files)
    
        for i in range(0,len(video_list)):
            for s in range(0, len(video_list[i])):
                int_video_list.append(int(video_list[i][s:s+1]))
        
        return int_video_list
            
    
    def ReadValue(self, options):
        print('RowCharacteristic read: ' + repr(self.values))
        return self.values


class VideoService(Service):
    SVC_UUID = '020a0df4-0c74-1a40-725e-01806fac4080'
    
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.SVC_UUID, True)
        self.add_characteristic(VideoChrc(bus, 0, self))


#######################################
###      Function Registration      ###
#######################################
 
class Func_Application(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(MotorService(bus, 0))
        self.add_service(VideoService(bus, 1))
 
 
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
