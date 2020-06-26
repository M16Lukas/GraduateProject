# test BLE Scanning software
# jcs 6/8/2014

import blescan
import sys
import bluetooth._bluetooth as bluez
import os
import time
import subprocess
import threading

class Distance(threading.Thread):
    queue = list()
    n = 0
    
    def __init__(self, rssi, txpower, _n):
        threading.Thread.__init__(self)
        self.rssi = rssi
        self.txpower = txpower
        self.n = _n
        
    def run(self):
        N = 5
        if self.rssi == 0:
            return -1.0 # if we can't determine accuracy, return -1
        
        ratio = self.txpower - self.rssi
        ratio2 = ratio / (10*N)
        d = pow(10, ratio2)
        
        # Move Avg Filter
        if len(self.queue) == self.n:
            avg = sum(self.queue) / self.n
            self.queue.pop()
            self.queue.insert(0, d)
        else:
            self.queue.insert(0, d)
            avg = sum(self.queue) / len(self.queue)
        
        return d, self.queue, avg
            

dev_id = 0
try:
    sock = bluez.hci_open_dev(dev_id)
    print (" *** Looking for BLE Beacons ***")
    print (" *** CTRL-C to Cancel ***")
except:
    print("error accessing bluetooth device...")
    sys.exit(1)

blescan.hci_le_set_scan_parameters(sock)
blescan.hci_enable_le_scan(sock)

try:
    while True:
        returnedList = blescan.parse_events(sock, 300)
        for beacon in returnedList:
            beacon_split = list(beacon.values())
            #print(beacon)
            if beacon_split[0] == "iBeacon":
                bt_rssi = beacon_split[4]
                bt_tx_power = beacon_split[5]
                bt_n = 5
                a, b, c = Distance(bt_rssi, bt_tx_power, bt_n).run()
                print("distance : ", a)
                print("queue    : ", b)
                print("avg      : ", c)
                print("")
except KeyboardInterrupt:
    pass
