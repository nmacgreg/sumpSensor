#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import sys

# Pin assignments
PIN_TRIGGER = 17
PIN_ECHO = 27

# Constants
SENSOR_MIN_DISTANCE = 2  # Sensor's minimum effective distance in cm
SUMP_DEPTH_CM = 55       # Distance from sensor to sump base in cm

def init_sensor():
    """Initialize GPIO settings for the HC-SR04 sensor."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_TRIGGER, GPIO.OUT)
    GPIO.setup(PIN_ECHO, GPIO.IN)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)
    #print("Waiting for sensor to settle...")
    time.sleep(2)

def measure_distance():
    """Send a trigger pulse and measure the echo response to calculate distance."""
    # Trigger the sensor
    GPIO.output(PIN_TRIGGER, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)

    # Measure the time for the echo response
    while GPIO.input(PIN_ECHO) == 0:
        pulse_start_time = time.time()
    while GPIO.input(PIN_ECHO) == 1:
        pulse_end_time = time.time()

    # Calculate distance in cm
    pulse_duration = pulse_end_time - pulse_start_time
    distance = round(pulse_duration * 17150, 2)
    return distance

def measurement_loop(count, warning_threshold, critical_threshold):
    """Take multiple distance measurements, calculate the average, and evaluate against thresholds."""
    distances = []
    
    for _ in range(count):
        distance = measure_distance()
        distances.append(distance)
        time.sleep(0.5)
    
    # Calculate average distance
    average_distance = round( sum(distances) / count)
    if average_distance < SENSOR_MIN_DISTANCE or average_distance > SUMP_DEPTH_CM:
        print("UNKNOWN - Water depth measurement of {average_distance} is out of range (valid: {SENSOR_MIN_DISTANCE} - {SUMP_DEPTH_CM})")
        sys.exit(3)

    # Determine Nagios plugin status
    if average_distance <= critical_threshold:
        print(f"CRITICAL - Average distance {average_distance} cm exceeds critical threshold of {critical_threshold} cm")
        sys.exit(2)
    elif average_distance <= warning_threshold:
        print(f"WARNING - Average distance {average_distance} cm exceeds warning threshold of {warning_threshold} cm")
        sys.exit(1)
    else:
        print(f"OK - Average distance {average_distance} cm within safe range")
        sys.exit(0)

def main():
    """Main function to initialize the sensor, run measurements, and cleanup GPIO."""
    if len(sys.argv) != 4:
        print("Usage: script.py <num_measurements> <warning_threshold> <critical_threshold>")
        sys.exit(3)

    num_measurements = int(sys.argv[1])
    warning_threshold = float(sys.argv[2])
    critical_threshold = float(sys.argv[3])

    init_sensor()
    try:
        measurement_loop(num_measurements, warning_threshold, critical_threshold)
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
