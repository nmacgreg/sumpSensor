#!/usr/bin/python3

from webthing import (Action, Event, Property, SingleThing, Thing, Value,
                      WebThingServer)
import logging
import uuid
import subprocess
import RPi.GPIO as GPIO
import time

def initialize_sensor():

    #try:
      GPIO.setmode(GPIO.BCM)

      GPIO.setup(PIN_TRIGGER, GPIO.OUT)
      GPIO.setup(PIN_ECHO, GPIO.IN)

      GPIO.output(PIN_TRIGGER, GPIO.LOW)

      #print "Waiting for sensor to settle"

      time.sleep(2)

      return 0

def depth():
    # An initial rough measure of the depth of the sump pit, dry.  This will need adjusting after final install. 
    # This should likely be read from a file. 
    calibrationDepth=60 

    #try:

      #print "Strobe the trigger"
    GPIO.output(PIN_TRIGGER, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)

    # measuring the time until a response...
    while GPIO.input(PIN_ECHO)==0:
                    pulse_start_time = time.time()
    while GPIO.input(PIN_ECHO)==1:
                    pulse_end_time = time.time()

    pulse_duration = pulse_end_time - pulse_start_time
    distance = round(pulse_duration * 17150, 2) # speed of sound in air!
    #print "Distance:",distance,"cm"
    depth = calibrationDepth - distance

    return depth

def make_thing():
    thing = Thing('Water Depth Sensor', ['MultiLevelSensor'], 'Depth of water in sump')

    thing.add_property(
        Property(thing,
                 'depth',
                 Value(depth()),
                 metadata={
                     '@type': 'LevelProperty',
                     'label': 'cm',
                     'type': 'number',
                     'description': 'The depth of the water in my sump pit',
                     'minimum': 0,
                     'maximum': 66,
                     'unit': 'cm',
                 }))

    return thing


def run_server():
    thing = make_thing()

    # If adding more than one thing, use MultipleThings() with a name.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(SingleThing(thing), port=8888)
    try:
        logging.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        logging.info('stopping the server')
        server.stop()
        logging.info('done')

if __name__ == '__main__':
    logging.basicConfig(
        level=10,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )

    PIN_TRIGGER = 23
    PIN_ECHO = 24
    initialize_sensor()

    run_server()

#finally:
    GPIO.cleanup()
