#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import configparser
from flask import Flask, jsonify
from collections import deque
import threading

# Configuration defaults
CONFIG_PATH = "/etc/sumpSensor/sumpSensor.conf"
DEFAULT_AVERAGE_READINGS = 5
DEFAULT_FREQUENCY_SEC = 60  # Measure every 60 seconds by default
DEFAULT_SAMPLE_DEPTH = 10

# Initialize Flask app
app = Flask(__name__)

# Initialize variables for measurements and state
average_readings = DEFAULT_AVERAGE_READINGS
measurement_frequency = DEFAULT_FREQUENCY_SEC
sample_depth = DEFAULT_SAMPLE_DEPTH
measurements = deque(maxlen=sample_depth)
current_rate = 0.0  # Filling rate in liters per minute

# State variables
filling = None
latest_measurement = None


def init_sensor():
    """Initialize GPIO settings for the HC-SR04 sensor."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_TRIGGER, GPIO.OUT)
    GPIO.setup(PIN_ECHO, GPIO.IN)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)
    print("Waiting for sensor to settle...")
    time.sleep(2)


def measure_distance():
    """Send a trigger pulse and measure the echo response to calculate distance."""
    GPIO.output(PIN_TRIGGER, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)

    while GPIO.input(PIN_ECHO) == 0:
        pulse_start_time = time.time()
    while GPIO.input(PIN_ECHO) == 1:
        pulse_end_time = time.time()

    pulse_duration = pulse_end_time - pulse_start_time
    distance = round(pulse_duration * 17150)
    return distance


def get_average_distance(count):
    """Take multiple measurements and return the average."""
    distances = []
    for _ in range(count):
        distance = measure_distance()
        if distance < SENSOR_MIN_DISTANCE or distance > SUMP_DEPTH_CM:
            return None  # Out of range; should handle in the Nagios check
        distances.append(distance)
        time.sleep(0.5)

    return sum(distances) / count if distances else None


def monitor_sump():
    """Monitor the sump, updating measurements and detecting state changes."""
    global latest_measurement, filling, current_rate

    while True:
        latest_measurement = get_average_distance(average_readings)
        if latest_measurement:
            measurements.append(latest_measurement)
            calculate_fill_rate()
            update_state()
        
        time.sleep(measurement_frequency)


def calculate_fill_rate():
    """Calculate the rate at which the sump is filling in liters per minute."""
    if sump_dimension_x > 0 and sump_dimension_y > 0 and len(measurements) >= 2:
        area_cm2 = sump_dimension_x * sump_dimension_y
        change_in_depth_cm = measurements[-2] - measurements[-1]  # Depth change in cm
        volume_change_cm3 = area_cm2 * change_in_depth_cm  # Volume in cubic cm
        volume_change_liters = volume_change_cm3 / 1000  # Convert to liters

        time_interval_min = measurement_frequency / 60  # Convert frequency to minutes
        current_rate = volume_change_liters / time_interval_min


def update_state():
    """Update the filling status based on recent measurements."""
    global filling
    if len(measurements) >= 2:
        if measurements[-1] < measurements[-2]:
            filling = "filling"
        elif measurements[-1] > measurements[-2]:
            filling = "emptying"
        else:
            filling = "static"


@app.route('/api/average_depth', methods=['GET'])
def get_average_depth():
    """API route to get the most recent averaged measurement."""
    return jsonify({"average_depth_cm": latest_measurement})


@app.route('/api/state', methods=['GET'])
def get_state():
    """API route to get the current state of the sump (filling, emptying, static)."""
    return jsonify({"state": filling})


@app.route('/api/fill_rate', methods=['GET'])
def get_fill_rate():
    """API route to get the current fill rate in liters per minute."""
    return jsonify({"fill_rate_liters_per_minute": current_rate})


def load_config():
    """Load configuration file and set parameters."""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    global average_readings, measurement_frequency, sample_depth, sump_dimension_x, sump_dimension_y, PIN_TRIGGER, PIN_ECHO, SENSOR_MIN_DISTANCE, SUMP_DEPTH_CM
    average_readings = config.getint('Settings', 'readings_to_average', fallback=DEFAULT_AVERAGE_READINGS)
    measurement_frequency = config.getint('Settings', 'measurement_frequency', fallback=DEFAULT_FREQUENCY_SEC)
    sample_depth = config.getint('Settings', 'sample_depth', fallback=DEFAULT_SAMPLE_DEPTH)
    sump_dimension_x = config.getint('Settings', 'sump_dimension_x', fallback=60)
    sump_dimension_y = config.getint('Settings', 'sump_dimension_y', fallback=60)
    PIN_TRIGGER = config.getint('Settings', 'PIN_TRIGGER', fallback=17)
    PIN_ECHO = config.getint('Settings', 'PIN_ECHO', fallback=27)
    SENSOR_MIN_DISTANCE  = config.getint('Settings', 'SENSOR_MIN_DISTANCE', fallback=2) 
    SUMP_DEPTH_CM = config.getint('Settings', 'SUMP_DEPTH_CM', fallback=55)



if __name__ == "__main__":
    load_config()
    init_sensor()
    
    # Start monitoring thread
    monitoring_thread = threading.Thread(target=monitor_sump)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    # Start the Flask API server
    app.run(host="0.0.0.0", port=5000)

