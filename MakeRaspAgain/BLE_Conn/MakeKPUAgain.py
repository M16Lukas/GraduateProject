"""
- Title  : Bicycle Smart Lock
- Writer : Minho Park
- Data   : 29-05-2020 
"""

#######################################
######### import libraries. ###########
#######################################

# system
import sys
import os
import time
import subprocess
import threading
import queue

# bluetooth
import bluetooth._bluetooth as bluez
import bluetooth
import blescan

# GPIO
import RPi.GPIO as GPIO

#######################################
############ Const Values. ############
#######################################

# Target (RECO)
MY_UUID = "24ddf411-8cf1-440c-87cd-e368daf9c93e"
MY_MAJOR = 501
MY_MINOR = 3015

# GPIO
GPIO_LED = 17

# Setting up GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_LED, GPIO.OUT, initial=GPIO.LOW) # using GPIO 17(PIN Number : 11)

# Check if there is already running process.
process = subprocess.check_output(["ps", "-ef"])
process_split = process.splitlines()
process_count = 0
for item in process_split:
    if "MakeKPUAgain".encode() in item:
        print(item)
        process_count = process_count + 1
if process_count > 2:
    print("----- MKA already running... exit -----")
    

# setting up iBeacon scanning related
dev_id = 0
try:
    sock = bluez.hci_open_dev(dev_id)
except:
    print("error accessing bluetooth device...")
    sys.exit(1)

blescan.hci_le_set_scan_parameters(sock)
blescan.hci_enable_le_scan(sock)

# Calculating beacon distance
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

#######################################
############### Working. ##############
#######################################

try:
    f = open("/etc/MakeKPUAgain.conf", 'r')
    conf_uuid = f.readline()
    if conf_uuid:
        MY_UUID = conf_uuid[:-1]
        conf_major = f.readline()
        if conf_major:
            MY_MAJOR = conf_major[:-1]
            conf_minor = f.readline()
            if conf_minor:
                MY_MINOR = conf_minor[:-1]
    f.close()
except Exception as e:
    print("---- Conf not found ----")
    
print("---------------- Init -------------------")
print("UUID  :", MY_UUID)
print("Major :", MY_MAJOR)
print("Minor :", MY_MINOR)

while True:
    try:
        returnedList = blescan.my_parse_events(sock, 300, target=MY_UUID)
        
        matchCnt = 0
        for beacon in returnedList:
            beacon_split = list(beacon.values())
            if beacon_split[1] == MY_UUID and beacon_split[2] == MY_MAJOR and beacon_split[3] == MY_MINOR:
                print("found beacon : %s" % beacon)
                matchCnt += 1
            
        if matchCnt >= 1:
            beacon_distance = Distance(beacon_split[4], beacon_split[5]).run()
            avg_beacon_distance = MoveAvgFilter(3).moveAvgFilter(beacon_distance)
            if avg_beacon_distance <= 3:
                print("distance :" + str(avg_beacon_distance) + " stable")
                GPIO.output(GPIO_LED, True)
            else:
                print("distance : " + str(avg_beacon_distance) + " too far")
                GPIO.output(GPIO_LED, False)
        else:
            GPIO.output(GPIO_LED, False)

    except KeyboardInterrupt as e:
        print("Main Exception : ", e)
        thread_flag = False
        os._exit(1)

thread_flag = False
os._exit(1)