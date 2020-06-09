import subprocess
import socket
import blescan
import sys
import bluetooth._bluetooth as bluez
from time import sleep

bct_BLUETOOTHDEVICE = "hci0"
bct_OGF = "0x08"
bct_OCF_format = "0x0008"
bct_OCF_setting = "0x0006"
bct_OCF_operate = "0x000A"
bct_start = "01"
bct_stop = "00"

"""
Data(0-31 bytes)
"""
bct_IBEACONPROFIX = "0x1E 0x02 0x01 0x1A 0x1A 0xFF 0x4C 0x00 0x02 0x15" # iBeacon prefix(9 bytes)
bct_UUID = "0x00 0x00 0x00 0xAC 0xE8 0xB4 0xE0 0xC2 0x7D 0x20 0xB6 0x11 0xB6 0x11 0xC7 0x74" # Proximity UUID(16 bytes)
bct_MAJOR = "0x00 0x01" # Major(2 bytes)
bct_MINOR = "0x00 0x00" # Minor(2 bytes)
bct_POWER = "0xc8" # TX power(2 bytes)

def beacon_TX_config(_param):
    result = subprocess.check_output("sudo hciconfig " + bct_BLUETOOTHDEVICE
                                     + " " + _param, shell=True)
    
def beacon_TX_cmd_format(_ocf, _ibeaconprofix, _uuid, _major, _minor, _power):
    _bct_ogf = bct_OGF + " "
    _ocf = _ocf + " "
    _ibeaconprofix = _ibeaconprofix + " "
    _uuid = _uuid + " "
    _major = _major + " "
    _minor = _minor + " "
    result = subprocess.check_output("sudo hciconfig " + bct_BLUETOOTHDEVICE +
                                     " cmd " + _bct_ogf + _ocf + _ibeaconprofix +
                                     _uuid + _major + _minor + _power, shell=True)
    
def beacon_TX_cmd_setting(_ocf, _interval):
    _bct_ogf = bct_OGF +" "
    _ocf = _ocf + " "
    _intervalHEX = '{:04X}'.format(int(_interval/0.625))
    _minInterval = _intervalHEX[2:] + " " + _intervalHEX[:2] + " "
    _maxInterval = _intervalHEX[2:] + " " + _intervalHEX[:2] + " "
    result = subprocess.check_output("sudo hciconfig " + bct_BLUETOOTHDEVICE +
                                     " cmd " + _bct_ogf + _ocf + _minInterval +
                                     _maxInterval + "00 00 00 00 00 00 00 00 00 07 00"
                                     ,shell=True)

def beacon_TX_cmd_operate(_ocf, _param):
    _bct_ogf = bct_OGF + " "
    _ocf = _ocf + " "
    result = subprocess.check_output("sudo hciconfig " + bct_BLUETOOTHDEVICE +
                                     " cmd " + _bct_ogf + _ocf + _param, shell=True)
    
def beacon_TX_DevTrigger(_str):
    _bct_uuid = "00 00 " +_str + " AC E8 B4 E0 C2 7D 20 B6 11 B6 11 C7 74"
    beacon_TX_cmd_format(bct_OCF_format, bct_IBEACONPROFIX, _bct_uuid, bct_MAJOR,
                         bct_MINOR, bct_POWER)
    sleep(1)
    
beacon_TX_config("up")
beacon_TX_cmd_format(bct_OCF_format, bct_IBEACONPROFIX, bct_UUID, bct_MAJOR,
                         bct_MINOR, bct_POWER)
beacon_TX_cmd_setting(bct_OCF_setting, 100)
beacon_TX_cmd_operate(bct_OCF_operate, bct_start)

try:
    print("BLE EMIT START")
    while True:
        beacon_TX_DevTrigger("21")
finally:
    print('BLE EMIT STOP')
    beacon_TX_cmd_operate(bct_OCF_operate, bct_stop)