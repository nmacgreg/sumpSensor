# Sump Sensor

Ever needed both a daemon that can monitor the status of the HC-SR01 sensor in your sump, and respond to queries from both Nagios and Prometheus?
Then this is for you!

## Some prerequisites

* This is tested only on Raspberry Pi OS
* You need gunicorn installed: `sudo apt install gunicorn` (there are other ways to get this installed)


## For Testing purposes

* Start the process in one terminal: `gunicorn --workers 1 --bind 0.0.0.0:5000 sumpSensor:app`
* Test the route Nagios will use (depth of the water, in cm): `curl http://localhost:5000/api/average_depth`
* Test the Prometheus route: `curl -s http://localhost:5000/metrics | tail -6
* Reveal the current state, eg static, filling, or emptying: `curl http://localhost:5000/api/state`
* Reveal the rate at which the sump is filling (or emptying), in litres per minute: `curl http://localhost:5000/api/fill_rate`
* (Perhaps open port 5000 on your firewall, for testing remotely?)

---

## Awareness of Inaccuracy

* Rasperry Pi OS is not an RTOS
* The nature of this sensor is highly based on *time*
* This code is moderately complex, with separate threads, multiple calculations, maintaining state, Flask and prometheus interfaces...
* All those features can introduce timing delays, and since we're measuring using the speed-of-sound, tiny delays during the measurement routine could mean that the measurements are inaccurate
* I'm certainly getting jitter at millimeter resolution - but I only need centimeters, so this is fine for my purposes!
