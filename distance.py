#!/usr/bin/python
# See: https://pimylifeup.com/raspberry-pi-distance-sensor/
# I didn't write this code.  I just copied it from the URL above, and modified 
# the GPIO mode and pins to match the circuit I set up for measure.py.
import RPi.GPIO as GPIO
import time

def init_sensor():

      GPIO.setmode(GPIO.BCM)

      # setup 2 pins needed for this project
      GPIO.setup(PIN_TRIGGER, GPIO.OUT)  # this is an output pin
      GPIO.setup(PIN_ECHO, GPIO.IN)      # this is an input pin

      GPIO.output(PIN_TRIGGER, GPIO.LOW) # Start this pin, set it to 0

      print ("Waiting for sensor to settle...")
      time.sleep(2)

def measurement_loop(limit):
      counter=0
      while counter < limit:
          # Strobe the trigger
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
          print ("Distance:",distance,"cm")
          time.sleep(0.5)
          counter += 1


# Main...

#bad global vars
#PIN_TRIGGER = 23
#PIN_ECHO = 24
PIN_TRIGGER = 17
PIN_ECHO = 27

init_sensor()
measurement_loop(5)
GPIO.cleanup()
