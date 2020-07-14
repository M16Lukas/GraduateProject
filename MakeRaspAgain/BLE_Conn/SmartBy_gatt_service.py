#!/usr/bin/python
"""
- Title  : Bicycle Smart Lock
- Writer : Minho Park
- Date   : 13-07-2020 
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

#######################################
###     Linear Actuator Control     ###
#######################################

# Setting up GPIO
GPIO_LOCK = 18
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_LOCK, GPIO.OUT)     # using GPIO 18

"""
Linear Actuator(L12-30-100-6-R)
- Stroke Length       = 30 mm
- Gear reduction Rate = 100
- Voltage             = 6 Volt (DC)
- Controller          = R (RC Servo Integrated)
"""

# Lock On & Off
class LockOnOff(threading.Thread):

    lock_pwm = GPIO.PWM(GPIO_LOCK, 500)   # Frequency = 0.5 kHz (2 ms)
    lock_pwm.start(100)                   # Duty Cycle = 100
    check_int = 0
    
    def __init__(self):
        threading.Thread.__init__(self)
    
    # 1.0 ms pulse commands the controller to fully retract the actuator 
    def On(self):
        for dc in range(95,101,1):
            self.lock_pwm.ChangeDutyCycle(dc)
            sleep(0.1)
            if dc == 100:
                check_int = 50
                self.Stop()

    # 2.0 ms pulse signals it to fully extend
    def Off(self):
        for dc in range(48,40,-1):
            self.lock_pwm.ChangeDutyCycle(dc)
            sleep(0.1)
            if dc == 41:
                check_int = -50
                self.Stop()

    def Stop(self):
        for dc in range(0,20,1):
            self.lock_pwm.ChangeDutyCycle(dc)
            sleep(0.5)


# Confirm entered password
def check_password(values):
    Crypto_Code = [0x01, 0x0f, 0x05, 0x0d, 0x08, 0x0b]
    ch = np.equal(Crypto_Code, values)
    if False in ch:
        LockOnOff().On()
    else:
        LockOnOff().Off()


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
        vla = []
        vlla = []
        for files in files_list:
            files = files.replace('-','')
            files = files.replace(':','')
            files = files.replace(' ','')
            files = files[:12]              # remove '.h264'
            vla.append(files)
    
        for i in range(0,len(vla)):
            for s in range(0, len(vla[i])):
                vlla.append(int(vla[i][s:s+1]))
        
        return vlla
            
    
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
        lock_pwm.stop()
        GPIO.cleanup()
        os._exit(1)
    
    lock_pwm.stop()
    GPIO.cleanup()
    os._exit(1)
 
 
if __name__ == '__main__':
    main()
