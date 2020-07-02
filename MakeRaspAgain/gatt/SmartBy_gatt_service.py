import dbus
import dbus.mainloop.glib
from time import sleep, time
 
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject
 
from bluez_components import *
 
mainloop = None

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
 
 
class MotorService(Service):
    DKDK_SVC_UUID = '0d0f0fe1-0e65-1d70-855e-02505f9c40e0'
 
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.DKDK_SVC_UUID, True)
        self.add_characteristic(cmdChrc(bus, 0, self))
 
 
class MotorApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(MotorService(bus, 0))
 
 
class MotorAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(MotorService.DKDK_SVC_UUID)
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