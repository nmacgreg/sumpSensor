# Overview

The purpose of this repository is to develop and share software that reports the 
depth of the water in my sump pit.  The ultimate goal is to generate an alert if the sump is 
*too full*, indicating a problem that needs urgent resolution (flooding imminent).

I'm using an ultrasonic "time-of-flight" distance measuring sensor, HC-SR04. These sensors are 
pretty common, making an appearance in many "Learning Arduino/Learning RasPi" kits on Amazon & Adafruit.


# Environment

* Hardware:  Rasberry Pi 3 Model B v1.2 (should work on most RasPi)
* OS: Rasbian v3.0.0
* Sensor: HC-SR04 

# The Software

I've added 2 scripts that mostly work.  I have shockingly little Python experience, and no experience 
with WebThings, so these are initial steps in prototyping: 

* distance.py works the best.
* measure.py seems to have some bugs.

Oh: I've just realized, there is no need to write my own code for this sensor. 
I'm sure someone has already done it.  I just need to find it.

Oh: https://github.com/alaudet/hcsr04sensor
> sudo pip  install hcsr04sensor
> sudo pip3 install hcsr04sensor

---

You can run this on the commandline, for testing: 

> python3 dynamic-sensor.py

You can manually throw it into the background:

> nohup python3 dynamic-sensor.py > /dev/null 2>&1 & 

---

You can install this and run it as a proper service: 
```bash
> sudo cp depthsensor.serve /lib/systemd/system/
> sudo chmod 644 /lib/systemd/system/depthsensor.serv
> sudo systemctl daemon-reload
> sudo systemctl enable depthsensor
> sudo systemctl start depthsensor
```

---

# Packaging

I'm really a Fedora guy; building an RPM would be trivial, but I have no experience building packages for Debian/Raspbian.
Anybody got any ideas?
