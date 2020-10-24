import neopixel
import board
import time

neo_pin = board.D18		# GPIO PIN
neo_cnt = 8				# Number of LED pixels 
neo_brightness = 0.2	# LED brightness

pixels = neopixel.NeoPixel(neo_pin, neo_cnt, brightness = neo_brightness)

pixels.fill((0,255,0)) # Green
pixels.show()
time.sleep(2)
pixels.fill((0,0,0))
pixels.show()
time.sleep(2)
