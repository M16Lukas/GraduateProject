from __future__ import print_function
from time import sleep, time

import sys
import os
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service

import array
import threading
import functools

import RPi.GPIO as GPIO
import numpy as np
import subprocess as sp

try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject

from random import randint

import exceptions
import adapters

BLUEZ_SERVICE_NAME = 'org.bluez'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'

GATT_MANAGER_IFACE = 'org.bluez.GattManager1'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE =    'org.bluez.GattDescriptor1'



class Application(threading.Thread, dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        threading.Thread.__init__(self)
        
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(MotorService(bus, 0))
        self.add_service(VideoService(bus, 1))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response


class Service(threading.Thread, dbus.service.Object):
    """
    org.bluez.GattService1 interface implementation
    """
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus, index, uuid, primary):
        threading.Thread.__init__(self)
        
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_SERVICE_IFACE: {
                        'UUID': self.uuid,
                        'Primary': self.primary,
                        'Characteristics': dbus.Array(
                                self.get_characteristic_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise exceptions.InvalidArgsException()

        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(threading.Thread, dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, service):
        threading.Thread.__init__(self)
        
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_CHRC_IFACE: {
                        'Service': self.service.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                        'Descriptors': dbus.Array(
                                self.get_descriptor_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise exceptions.InvalidArgsException()

        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print('Default ReadValue called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        print('Default StartNotify called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        print('Default StopNotify called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class Descriptor(threading.Thread, dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        threading.Thread.__init__(self)
        
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_DESC_IFACE: {
                        'Characteristic': self.chrc.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_DESC_IFACE:
            raise exceptions.InvalidArgsException()

        return self.get_properties()[GATT_DESC_IFACE]

    @dbus.service.method(GATT_DESC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print('Default ReadValue called, returning error')
        raise exceptions.NotSupportedException()

    @dbus.service.method(GATT_DESC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise exceptions.NotSupportedException()


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
            ['read', 'notify'],
            service)
        self.notifying = False
        self.value = []
        
    def videoFile(self, path):
        files_list = os.listdir(path)
        return files_list
    
    def ReadValue(self, options):
        self.value = self.videoFile(self.savepath)
        print('RowCharacteristic read: ' + repr(self.value))
        return [dbus.Byte(i) for i in self.value]
    
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


def register_app_cb():
    print('GATT application registered')


def register_app_error_cb(mainloop, error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()


def gatt_server_main(mainloop, bus, adapter_name):
    adapter = adapters.find_adapter(bus, GATT_MANAGER_IFACE, adapter_name)
    if not adapter:
        raise Exception('GattManager1 interface not found')

    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

    app = Application(bus)

    print('Registering GATT application...')

    service_manager.RegisterApplication(app.get_path(), {},
                                    reply_handler=register_app_cb,
                                    error_handler=functools.partial(register_app_error_cb, mainloop))
