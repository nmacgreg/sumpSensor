#!/usr/bin/python
import RPi.GPIO as GPIO
import time
import configparser
from flask import Flask, jsonify
from collections import deque
import prometheus_client
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST
import threading
import logging
import sys

# Configure logging, for running under gunicorn & systemd
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

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

# Prep for Prometheus interface
# Define a Prometheus gauge metric for water depth
water_depth_gauge = Gauge('sump_water_depth_cm', 'Depth of water in the sump in centimeters')
sump_fill_rate_gauge = Gauge('sump_fill_rate_liters_per_min', 'Rate of fill or empty, in liters per minute')

def init_sensor():
    """Initialize GPIO settings for the HC-SR04 sensor."""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_TRIGGER, GPIO.OUT)
    GPIO.setup(PIN_ECHO, GPIO.IN)
    GPIO.output(PIN_TRIGGER, GPIO.LOW)
    logger.info("Waiting for sensor to settle...")
    time.sleep(2)

initialized = False

def initialize():
    global initialized
    if initialized:
        return
    load_config()
    init_sensor()
    monitoring_thread = threading.Thread(target=monitor_sump)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    initialized = True

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
    distance = round(pulse_duration * 17150, 2)
    return distance


def get_average_distance(count):
    """Take multiple measurements and return the average."""
    distances = []
    for _ in range(count):
        distance = measure_distance()
        # need more error handling, here!
        if distance < SENSOR_MIN_DISTANCE or distance > SUMP_DEPTH_CM:
            logger.warning("Sensor returned an unusable value: %s", distance)
            return None  # Out of range; should handle in the Nagios check
        logger.info("Took a valid measurement: %s cm", distance)
        distances.append(distance)
        time.sleep(0.25)

    return round(sum(distances) / count) if distances else None


def monitor_sump():
    """Monitor the sump, updating measurements and detecting state changes."""
    global latest_measurement, filling, current_rate

    while True:
        latest_measurement = get_average_distance(average_readings)
        if latest_measurement:
            measurements.append(latest_measurement)
            calculate_fill_rate()
        
        time.sleep(measurement_frequency)


def calculate_fill_rate():
    """Calculate the rate at which the sump is filling in liters per minute using all available measurements."""
    global filling, RATE_THRESHOLD
    filling = "static"      # Default value if calculations fail
    if sump_dimension_x > 0 and sump_dimension_y > 0 and len(measurements) >= 2:
        area_cm2 = sump_dimension_x * sump_dimension_y

        # Generate a time vector in minutes based on measurement frequency
        times_min = [i * (measurement_frequency / 60) for i in range(len(measurements))]

        # Least-squares linear regression to estimate slope (depth per minute)
        n = len(measurements)
        sum_t = sum(times_min)
        sum_d = sum(measurements)
        sum_t2 = sum(t * t for t in times_min)
        sum_td = sum(t * d for t, d in zip(times_min, measurements))

        denominator = n * sum_t2 - sum_t ** 2
        if denominator == 0:
            return 0.0  # Avoid divide-by-zero if all time samples are the same

        slope_cm_per_min = (n * sum_td - sum_t * sum_d) / denominator

        # Convert depth change into volume change
        volume_change_cm3_per_min = slope_cm_per_min * area_cm2
        volume_change_liters_per_min = volume_change_cm3_per_min / 1000.0

        if volume_change_liters_per_min > RATE_THRESHOLD:
            filling = "filling"
        elif volume_change_liters_per_min < -RATE_THRESHOLD:
            filling = "emptying"
        else:
            filling = "static"

        return volume_change_liters_per_min

    return 0.0

# Initialize the sensor, and start a thread responsible for collecting measurements from it
@app.before_first_request
def startup():
    initialize()

@app.route('/api/average_depth', methods=['GET'])
def get_average_depth():
    """API route to get the most recent averaged measurement."""
    if latest_measurement: 
        water_depth = SUMP_DEPTH_CM - latest_measurement
        return jsonify({"average_depth_cm": water_depth})
    else:
        return jsonify({"average_depth_cm": "UNKNOWN"})
        


@app.route('/api/state', methods=['GET'])
def get_state():
    """API route to get the current state of the sump (filling, emptying, static)."""
    return jsonify({"state": filling})


@app.route('/api/fill_rate', methods=['GET'])
def get_fill_rate():
    """API route to get the current fill rate in liters per minute."""
    return jsonify({"fill_rate_liters_per_minute": current_rate})

# Add a new endpoint for Prometheus metrics
@app.route('/metrics', methods=['GET'])
def metrics():
    water_depth=-1
    global latest_measurement, current_rate
    # Update the gauge with current water depth
    if latest_measurement: 
        water_depth = SUMP_DEPTH_CM - latest_measurement
    water_depth_gauge.set(water_depth)
    sump_fill_rate_gauge.set(current_rate)

    # Generate and return metrics in Prometheus format
    return generate_latest(prometheus_client.REGISTRY), 200, {'Content-Type': CONTENT_TYPE_LATEST}

def load_config():
    """Load configuration file and set parameters."""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    global average_readings, measurement_frequency, sample_depth, sump_dimension_x, sump_dimension_y, PIN_TRIGGER, PIN_ECHO, SENSOR_MIN_DISTANCE, SUMP_DEPTH_CM, RATE_THRESHOLD
    average_readings = config.getint('Settings', 'readings_to_average', fallback=DEFAULT_AVERAGE_READINGS)
    measurement_frequency = config.getint('Settings', 'measurement_frequency', fallback=DEFAULT_FREQUENCY_SEC)
    sample_depth = config.getint('Settings', 'sample_depth', fallback=DEFAULT_SAMPLE_DEPTH)
    sump_dimension_x = config.getfloat('Settings', 'sump_dimension_x', fallback=60)
    sump_dimension_y = config.getfloat('Settings', 'sump_dimension_y', fallback=60)
    PIN_TRIGGER = config.getint('Settings', 'PIN_TRIGGER', fallback=17)
    PIN_ECHO = config.getint('Settings', 'PIN_ECHO', fallback=27)
    SENSOR_MIN_DISTANCE  = config.getint('Settings', 'SENSOR_MIN_DISTANCE', fallback=2) 
    SUMP_DEPTH_CM = config.getfloat('Settings', 'SUMP_DEPTH_CM', fallback=55)
    RATE_THRESHOLD = config.getfloat('Settings', 'RATE_THRESHOLD', fallback=0.1)


if __name__ == "__main__":
    load_config()
    init_sensor()
    
    # Start monitoring thread
    monitoring_thread = threading.Thread(target=monitor_sump)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    # Start the Flask API server
    app.run(host="0.0.0.0", port=5000)

