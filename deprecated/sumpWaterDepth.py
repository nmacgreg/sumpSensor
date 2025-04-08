#!/usr/bin/python3

from webthing import (Action, Event, Property, SingleThing, Thing, Value,
                      WebThingServer)
import logging
import uuid
import subprocess
import RPi.GPIO as GPIO
import time
from hcsr04sensor import sensor


def depth():
    # This should likely be read from a file. 
    calibrationDepth=60 
    value = sensor.Measurement(PIN_TRIGGER, PIN_ECHO)  # this instantiates the object, setting up the sensor, as a side-effect
    distance = value.raw_distance()

    depth = calibrationDepth - distance

    return round (depth, 1)

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
                     'description': 'The depth of the water in sump pit',
                     'minimum': 0,
                     'maximum': 66,
                     'unit': 'cm',
                     'readOnly': True,
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
    # Create a distance reading with the hcsr04 sensor module

    run_server()

#finally:
    GPIO.cleanup()
