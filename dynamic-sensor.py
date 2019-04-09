from asyncio import sleep, CancelledError, get_event_loop
from webthing import (Action, Event, MultipleThings, Property, Thing, Value,
                      WebThingServer)
from hcsr04sensor import sensor
import RPi.GPIO as GPIO
import logging
import random
import time
import uuid

class GPIODepthSensor(Thing):
    """A water depth sensor which updates its measurement every few seconds."""

    def __init__(self):
        Thing.__init__(self, 'Water Depth Sensor', ['MultiLevelSensor'], 'Depth of water in sump')

        self.level = Value(0.0)
        self.add_property(
            Property(self,
                     'depth',
                     self.level,
                     metadata={
                         '@type': 'LevelProperty',
                         'label': 'Depth',
                         'type': 'number',
                         'description': 'The depth of the water in sump pit',
                         'minimum': 0,
                         'maximum': 60,
                         'unit': 'cm',
                         'readOnly': True,
                     }))

        logging.debug('starting the sensor update looping task')
        self.sensor_update_task = \
            get_event_loop().create_task(self.update_level())

    async def update_level(self):
        try:
            while True:
                await sleep(3)
                new_level = self.read_from_gpio()
                logging.debug('setting new sump depth level: %s', new_level)
                self.level.notify_of_external_update(new_level)
        except CancelledError:
            # We have no cleanup to do on cancellation so we can just halt the
            # propagation of the cancellation exception and let the method end.
            logging.debug('auto-update has been cancelled')
            pass
        except: 
            logging.debug('Unexpected error: ', sys.exc_info()[0])
            raise
    
    def cancel_update_level_task(self):
        self.sensor_update_task.cancel()
        get_event_loop().run_until_complete(self.sensor_update_task)
        GPIO.cleanup()

    @staticmethod
    def read_from_gpio():
        # These variables should likely be read from a file, or passed in as class variables
        calibrationDepth=60 
        PIN_TRIGGER = 23
        PIN_ECHO = 24
        # This likely performs raw set-up each time, instantiates a new object...  Should instantiate the object once, store it within this object, 
        # and reference it from there each time
        value = sensor.Measurement(PIN_TRIGGER, PIN_ECHO)  # this instantiates the object, setting up the sensor, as a side-effect
        distance = value.raw_distance()

        depth = calibrationDepth - distance

        return round (depth, 1)


def run_server():
    # Create a thing that represents my ultrasonic water depth sensor
    sensor = GPIODepthSensor()

    # If adding more than one thing, use MultipleThings() with a name.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(MultipleThings([sensor], 'DepthDevice'), port=8888)
    try:
        logging.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        logging.debug('canceling the sensor update looping task')
        sensor.cancel_update_level_task()
        logging.info('stopping the server')
        server.stop()
        logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(
        level=10,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )
    run_server()


