#!/usr/bin/python
"""
- Title  : Bicycle Smart Lock
- Writer : Minho Park
- Date   : 07-07-2020 
"""

import sys
import os
import time
import subprocess as np
import threading

import bluetooth

import RPi.GPIO as GPIO

#######################################
############ Const Values. ############
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
            time.sleep(0.1)
            if dc == 100:
                self.Stop()

    # 2.0 ms pulse signals it to fully extend
    def Off(self):
        for dc in range(48,40,-1):
            print(dc)
            lock_pwm.ChangeDutyCycle(dc)
            time.sleep(0.1)
            if dc == 41:
                self.Stop()

    def Stop(self):
        for dc in range(0,40,1):
            lock_pwm.ChangeDutyCycle(dc)
            time.sleep(0.5)


#######################################
############### Working. ##############
#######################################

# Check if there is already running process
process = np.check_output(["ps", "-ef"])
process_split = process.splitlines()
process_count = 0
for item in process_split:
    if "SmartBy".encode() in item:
        process_count = process_count + 1
if process_count > 2:
    print("----- File already running... exit -----")

# Main Function
while True:
    
    try:
        device_mac = ""
        matchCnt = 0
        
        connected_device_info = np.getoutput("hcitool con").split() # listed
        if len(connected_device_info) > 1:
            device_mac = connected_device_info[3]# MAC Address of connected Device(GATT client)
            matchCnt += 1

        # connected
        if matchCnt >= 1:
            LockOnOff().Off()
        # disconnected
        else:
            LockOnOff().On()


    except KeyboardInterrupt as e:
        print("Main Exception : ", e)
        lock_pwm.stop()
        GPIO.cleanup()
        os._exit(1)


lock_pwm.stop()
GPIO.cleanup()
os._exit(1)   