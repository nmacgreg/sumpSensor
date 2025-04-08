#!/usr/bin/python

# Neil: stolen from https://github.com/alaudet/hcsr04sensor
# Hint: sudo pip install hcrs04sensor

from hcsr04sensor import sensor

# Created by Al Audet
# MIT License

def main():
    '''Calculate the depth of a liquid in centimeters using a HCSR04 sensor
       and a Raspberry Pi'''

    trig_pin = 23
    echo_pin = 24

    hole_depth = 60  # centimeters

    # Create a distance reading with the hcsr04 sensor module
    value = sensor.Measurement(trig_pin,
                               echo_pin
                               )

    raw_measurement = value.raw_distance()

    # Calculate the liquid depth, in centimeters, of a hole filled with liquid
    liquid_depth = value.depth_metric(raw_measurement, hole_depth)
    print("Depth = {} centimeters".format(liquid_depth))

if __name__ == "__main__":
    main()
