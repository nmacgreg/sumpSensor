#!/usr/bin/python
# See: https://pimylifeup.com/raspberry-pi-distance-sensor/
# I didn't write this code.  I just copied it from the URL above, and modified 
# the GPIO mode and pins to match the circuit I set up for measure.py.
import RPi.GPIO as GPIO
import time

try:
      #GPIO.setmode(GPIO.BOARD)
      GPIO.setmode(GPIO.BCM)

      #PIN_TRIGGER = 7
      #PIN_ECHO = 11
      PIN_TRIGGER = 23
      PIN_ECHO = 24

      GPIO.setup(PIN_TRIGGER, GPIO.OUT)
      GPIO.setup(PIN_ECHO, GPIO.IN)

      GPIO.output(PIN_TRIGGER, GPIO.LOW)

      print "Waiting for sensor to settle"

      time.sleep(2)

      print "Strobe the trigger"
      GPIO.output(PIN_TRIGGER, GPIO.HIGH)
      time.sleep(0.00001)
      GPIO.output(PIN_TRIGGER, GPIO.LOW)

      # measuring the time until a response...
      while GPIO.input(PIN_ECHO)==0:
                      pulse_start_time = time.time()
      while GPIO.input(PIN_ECHO)==1:
                      pulse_end_time = time.time()

      pulse_duration = pulse_end_time - pulse_start_time
      distance = round(pulse_duration * 17150, 2)
      print "Distance:",distance,"cm"

finally:
      GPIO.cleanup()
