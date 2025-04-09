# Sump Sensor

Ever needed both a daemon that can monitor the status of the HC-SR01 sensor in your sump, and respond to queries from both Nagios and Prometheus?
Then this is for you!

sudo apt install gunicorn
gunicorn --workers 1 --bind 0.0.0.0:5000 sumpSensor:app


---

## Awareness of Inaccuracy

* Rasperry Pi OS is not an RTOS
* The nature of this sensor is highly based on *time*
* This code is moderately complex, with separate threads, multiple calculations, maintaining state, Flask and prometheus interfaces...
* All those features can introduce timing delays, and since we're measuring using the speed-of-sound, tiny delays during the measurement routine could mean that the measurements are inaccurate
* I'm certainly getting jitter at millimeter resolution - but I only need centimeters, so this is fine for my purposes!
