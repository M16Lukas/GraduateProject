import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

pir_pin = 7 # GPIO 7
GPIO.setup(pir_pin, GPIO.IN, GPIO.PUD_UP)

while True:
	if GPIO.input(pir_pin):
		tim = time.localtime()
		print(" %d:%d:%d Motion detected" % (tim.tm_hour, tim.tm_min, tim.tm_sec))
		time.sleep(2)
	else:
		print("No motion")
	time.sleep(1)
