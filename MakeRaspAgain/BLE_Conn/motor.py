import RPi.GPIO as GPIO
import sys
from time import sleep, time

# Init
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# Pin
Rght = 36 # BCM(16), IN1, Rght
Lft  = 38 # BCM(20), IN2, Lft
ENB  = 40 # BCM(21), PWM
    
# GPIO
GPIO.setup(Rght, GPIO.OUT)
GPIO.setup(Lft, GPIO.OUT)
GPIO.setup(ENB, GPIO.OUT)
        
# PWM
pwm = GPIO.PWM(ENB, 100)
pwm.start(0)

tim = 0.6

# Lock Function
def Lock_Close():
    print("lock close")
    GPIO.output(Rght, GPIO.HIGH)
    GPIO.output(Lft, GPIO.LOW)
    GPIO.output(ENB, GPIO.HIGH)

    for sp in range(26):
        print(sp)
        pwm.ChangeDutyCycle(sp)
        sleep(tim)
    stop()


def Lock_Open():
    print("lock open")
    GPIO.output(Rght, GPIO.LOW)
    GPIO.output(Lft, GPIO.HIGH)
    GPIO.output(ENB, GPIO.HIGH)

    for sp in range(50, 100, 1):
        print(sp)
        pwm.ChangeDutyCycle(sp)
        sleep(tim)
    stop()


def stop():
    print("stopping motor")
    GPIO.output(Rght, GPIO.LOW)
    GPIO.output(Lft, GPIO.LOW)
    GPIO.output(ENB, GPIO.LOW)
    GPIO.cleanup()


try:
    Lock_Close()
    #Lock_Open()
except KeyboardInterrupt:
    pwm.stop()
    GPIO.cleanup()
    sys.exit()

pwm.stop()	
GPIO.cleanup()
sys.exit()
		
