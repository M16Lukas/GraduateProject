import sys
import os
import time
import subprocess as np

import RPi.GPIO as GPIO

# Setting up GPIO
GPIO_LOCK = 18
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_LOCK, GPIO.OUT, initial=GPIO.LOW) # using GPIO 18

# Set Linear Actuator
lock_pwm = GPIO.PWM(GPIO_LOCK, 400) # 400 kHz
lock_pwm.start(100)
lock_on = 79
lock_off = 41

# Check if there is already running process
process = np.check_output(["ps", "-ef"])
process_split = process.splitlines()
process_count = 0
for item in process_split:
    if "ttt".encode() in item:
        #print(item)
        process_count = process_count + 1
if process_count > 2:
    print("----- File already running... exit -----")

while True:
    try:
        connected_device_info = np.getoutput("hcitool con").split()
        if len(connected_device_info) > 1:
            device_mac = connected_device_info[3] # MAC Address of connected Device(GATT client)
            lock_pwm.ChangeDutyCycle(lock_off)
            print("off")
        else:
            device_mac = ""
            lock_pwm.ChangeDutyCycle(lock_on)
            print("on")

    except KeyboardInterrupt as e:
        print("Main Exception : ", e)
        thread_flag = False
        GPIO.cleanup()
        os._exit(1)


thread_flag = False
GPIO.cleanup()
os._exit(1)   