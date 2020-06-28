"""
- Title  : Bicycle Smart Lock
- Writer : Minho Park
- Data   : 26-06-2020 
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

# Setting up GPIO
GPIO_LOCK = 18
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_LOCK, GPIO.OUT, initial=GPIO.LOW) # using GPIO 18

# Set Linear Actuator
lock_pwm = GPIO.PWM(GPIO_LOCK, 400) # 400 kHz
lock_pwm.start(0)
lock_on = 80
lock_off = 40

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
    queue = list()
    n = 0
    
    def __init__(self, rssi, txpower, _n):
        threading.Thread.__init__(self)
        self.rssi = rssi
        self.txpower = txpower
        self.n = _n
        
    def run(self):
        # Calculating Beacon Distance
        N = 5
        prev_rssi = 0
        if self.rssi == 0:
            # if we can't determine accuracy, return -1
            return -1.0
        else:
            # first noise of rssi filtering
            if self.rssi - prev_rssi >= 4.0:
                self.rssi = prev_rssi
            else:
                prev_rssi = self.rssi
        
        ratio = self.rssi*1.0/self.txpower
        if ratio < 1.0:
            d = pow(ratio, 10)
        else:
            d = 0.89976*pow(ratio,7.7095) + 0.111
        
        # filtering beacon distance by using Move Average Filter
        if len(self.queue) == self.n:
            avg = sum(self.queue) / self.n
            self.queue.pop()
            self.queue.insert(0, d)
        else:
            self.queue.insert(0, d)
            avg = sum(self.queue) / len(self.queue)
        
        return d, avg

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
print("-----------------------------------------")

"""
Main
"""
while True:
    try: 
        returnedList = blescan.my_parse_events(sock, 300, target=MY_UUID)
        
        matchCnt = 0
        for beacon in returnedList:
            beacon_split = list(beacon.values())
            if beacon_split[1] == MY_UUID and beacon_split[2] == MY_MAJOR and beacon_split[3] == MY_MINOR:
                #print("found beacon : %s" % beacon)
                matchCnt += 1
            
        if matchCnt >= 1:
            cnt = 0
            bt_rssi = beacon_split[4]
            bt_tx_power = beacon_split[5]
            bt_n = 10
            distance, avg_distance = Distance(bt_rssi, bt_tx_power, bt_n).run()
            print("distance : ", distance)
            print("avg      : ", avg_distance)
            print("")
            
            if avg_distance < 2.5:
                lock_pwm.ChangeDutyCycle(lock_off)
            else:
                lock_pwm.ChangeDutyCycle(lock_on)
        else:
            lock_pwm.ChangeDutyCycle(lock_on)

    except KeyboardInterrupt as e:
        print("Main Exception : ", e)
        thread_flag = False
        GPIO.cleanup()
        os._exit(1)

thread_flag = False
GPIO.cleanup()
os._exit(1)