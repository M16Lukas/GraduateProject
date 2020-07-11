#!/usr/bin/python
"""
- Title  : Bicycle Smart Lock
- Writer : Minho Park
- Date   : 12-07-2020 
"""

import sys
import os
import threading
import dbus
import dbus.mainloop.glib

from time import sleep, time

import RPi.GPIO as GPIO
import numpy as np
import subprocess as sp
 
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject
 
from bluez_components import *
 
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
lock_pwm = GPIO.PWM(GPIO_LOCK, 500)   # Frequency = 0.5 kHz (2 ms)
lock_pwm.start(100)                   # Duty Cycle = 100
class LockOnOff(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    # 1.0 ms pulse commands the controller to fully retract the actuator 
    def On(self):
        for dc in range(95,101,1):
            lock_pwm.ChangeDutyCycle(dc)
            sleep(0.1)
            if dc == 100:
                self.Stop()

    # 2.0 ms pulse signals it to fully extend
    def Off(self):
        for dc in range(48,40,-1):
            print(dc)
            lock_pwm.ChangeDutyCycle(dc)
            sleep(0.1)
            if dc == 41:
                self.Stop()

    def Stop(self):
        for dc in range(0,20,1):
            lock_pwm.ChangeDutyCycle(dc)
            sleep(0.5)


def check_password(value):
    Crypto_Code = [0x01, 0x0f, 0x05, 0x0d, 0x08, 0x0b]
    ch = np.equal(Crypto_Code, value)
    if False in ch:
        print("get out!!!!!")
        LockOnOff().On()
    else:
        print("come on buddy")
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
 
 
class MotorApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(MotorService(bus, 0))
 
 
class MotorAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(MotorService.SVC_UUID)
        self.include_tx_power = True


#######################################
###       Black Box Control         ###
#######################################

savepath = '/home/pi/MakeRaspAgain/VideoRecord'

class VideoChrc(Characteristic):
    CMD_UUID = '020a0df4-0c74-1a40-725e-01806fac4081'
 
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CMD_UUID, 
            ['read', 'notify'],
            service)
        self.notifying = False
        self.value = [ 0x00 for i in range(1024) ]
 
    def ReadValue(self, options):
        print('RowCharacteristic read: ' + repr(self.value))
        return self.value
    
    def StartNotify(self):
        if self.notifying:
            print("Already notifying, nothing to do")
            return
        
        self.notifying = True
    
    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return
        
        self.notifying = False


class VideoService(Service):
    SVC_UUID = '020a0df4-0c74-1a40-725e-01806fac4080'
    
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.SVC_UUID, True)
        self.add_characteristic(VideoChrc(bus, 0, self))


class VideoApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(VideoService(bus, 0))
 
 
class VideoAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(VideoService.SVC_UUID)
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
    app = MotorApplication(bus)
 
    # Create advertisement
    dkdk_advertisement = MotorAdvertisement(bus, 0)
 
    mainloop = GObject.MainLoop()
 
    # Register gatt services
    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
 
    # Register advertisement
    ad_manager.RegisterAdvertisement(dkdk_advertisement.get_path(), {},
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
