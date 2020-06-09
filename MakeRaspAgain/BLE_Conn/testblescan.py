# test BLE Scanning software
# jcs 6/8/2014

import blescan
import sys
import bluetooth._bluetooth as bluez
import os
import time
import subprocess
import threading
import queue

class Distance(threading.Thread):
    def __init__(self, rssi, txpower):
        threading.Thread.__init__(self)
        self.rssi = rssi
        self.txpower = txpower
        
    def run(self):
        N = 2
        if self.rssi == 0:
            return -1.0 # if we can't determine accuracy, return -1
        
        ratio = self.txpower - self.rssi
        ratio2 = ratio / (10*N)
        d = pow(10, ratio2)
        return d
    
class MoveAvgFilter(threading.Thread):
    prevAvg = 0          # previous Average
    xBuf = queue.Queue() # store The most recent n-points values
    n = 0                # reference Data count
    
    def __init__(self, _n):
        threading.Thread.__init__(self)
        # n init
        for _ in range(_n):
            self.xBuf.put(0)
            
        # saving reference Data count
        self.n = _n
    
    def moveAvgFilter(self, x):
        # Queue's first value = x_(k-n)
        front = self.xBuf.get()
        # This step put input value at the Queue
        self.xBuf.put(x)
        
        avg = self.prevAvg + (x - front) / self.n
        self.prevAvg = avg
        
        return avg
        

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
            a = Distance(beacon_split[4], beacon_split[5]).run()
            b = MoveAvgFilter(3).moveAvgFilter(a)
            print("distance : ", a, " meter")
            print("avg : ", b, " meter")
            print("")
except KeyboardInterrupt:
    pass
