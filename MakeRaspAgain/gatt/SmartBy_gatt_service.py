import dbus
import dbus.mainloop.glib
from time import sleep, time
import numpy as np
 
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject
 
from bluez_components import *
 
mainloop = None

def check_password(value):
    Crypto_Code = [0x01, 0x0f, 0x05, 0x0d, 0x08, 0x0b]
    ch = np.equal(Crypto_Code, value)
    if False in ch:
        print("get out!!!!!")
    else:
        print("come on buddy")

class cmdChrc(Characteristic):
    CMD_UUID = '0d0f0fe1-0e65-1d70-855e-02505f9c40e1'
 
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CMD_UUID, 
            ['read', 'write'],
            service)
        self.value = [ 0x00 for i in range(1024) ]
 
    def ReadValue(self, options):
        print('RowCharacteristic Read: ' + repr(self.value))
        return self.value
 
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
 
 
if __name__ == '__main__':
    main()