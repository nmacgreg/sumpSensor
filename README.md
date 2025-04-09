Ever needed both a daemon that can monitor the status of the HC-SR01 sensor in your sump, and respond to queries from both Nagios and Prometheus?
Then this is for you!

sudo apt install gunicorn
gunicorn --workers 1 --bind 0.0.0.0:5000 sumpSensor:app

