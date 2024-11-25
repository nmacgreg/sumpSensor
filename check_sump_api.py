#!/usr/bin/python
import requests
import sys

def check_sump_sensor(api_url, warning_threshold, critical_threshold):
    try:
        response = requests.get(f"{api_url}/api/average_depth")
        response.raise_for_status()
        data = response.json()
        average_distance = data["average_depth_cm"]

        if average_distance is None:
            print("UNKNOWN - No valid reading from sensor")
            sys.exit(3)

        if average_distance <= critical_threshold:
            print(f"CRITICAL - Average distance {average_distance} cm exceeds critical threshold of {critical_threshold} cm")
            sys.exit(2)
        elif average_distance <= warning_threshold:
            print(f"WARNING - Average distance {average_distance} cm exceeds warning threshold of {warning_threshold} cm")
            sys.exit(1)
        else:
            print(f"OK - Average distance {average_distance} cm within safe range")
            sys.exit(0)

    except requests.exceptions.RequestException as e:
        print(f"UNKNOWN - API request failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: nagios_check.py <api_url> <warning_threshold> <critical_threshold>")
        sys.exit(3)

    api_url = sys.argv[1]
    warning_threshold = float(sys.argv[2])
    critical_threshold = float(sys.argv[3])

    check_sump_sensor(api_url, warning_threshold, critical_threshold)
