import time
import json
import sys

from miio import MiotDevice, exceptions
from prometheus_client import start_http_server, Gauge

# --- MIoT Device Configuration ---
# MIOT_MAPPING for zhimi.airp.rmb1 (Xiaomi Smart Air Purifier 4 Lite)
# Check https://home.miot-spec.com/s/ for other devices.
MIOT_MAPPING = {
    # Service 2: Air Purifier
    'power': {'siid': 2, 'piid': 1},
    'fault': {'siid': 2, 'piid': 2},
    'mode': {'siid': 2, 'piid': 4},

    # Service 3: Environment
    'humidity': {'siid': 3, 'piid': 1},
    'aqi': {'siid': 3, 'piid': 4},      # AQI measured as PM2.5 concentration
    'temperature': {'siid': 3, 'piid': 7},

    # Service 4: Filter
    'filter_life_remaining': {'siid': 4, 'piid': 1},
    'filter_used_time': {'siid': 4, 'piid': 3},
    'filter_left_time': {'siid': 4, 'piid': 4},

    # Service 9: Custom Motor Settings
    'fan_speed_rpm': {'siid': 9, 'piid': 1},
    'favorite_level': {'siid': 9, 'piid': 11},       # Fan level for Favorite (Manual) mode
}

# --- Prometheus Metrics ---
power = Gauge('mi_purifier_power', 'Power status of the Purifier (1=on, 0=off)', ['name'])
mode = Gauge('mi_purifier_mode', 'Current operational mode as a number (0:Auto, 1:Sleep, 2:Manual)', ['name'])
aqi = Gauge('mi_purifier_aqi', 'AQI (PM2.5) from Purifier', ['name'])
temp = Gauge('mi_purifier_temp', 'Temperature from Purifier', ['name'])
humidity = Gauge('mi_purifier_humidity', 'Humidity from Purifier', ['name'])
fault = Gauge('mi_purifier_fault', 'Device fault code (0 means no fault)', ['name'])
fan_speed_rpm = Gauge('mi_purifier_fan_speed_rpm', 'Current fan speed in RPM', ['name'])
filter_life_remaining = Gauge('mi_purifier_filter_life_remaining_percent', 'Filter life remaining in percent', ['name'])
filter_used_time = Gauge('mi_purifier_filter_used_time', 'Filter used time', ['name'])
filter_left_time = Gauge('mi_purifier_filter_left_time', 'Filter time left in days', ['name'])
favorite_level = Gauge('mi_purifier_favorite_level', 'Custom fan level for Favorite mode', ['name'])


def exit_with_error(error):
    print(error, file=sys.stderr)
    sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        exit_with_error("JSON config file must be passed as the first argument")

    try:
        with open(sys.argv[1]) as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        exit_with_error(f"Error reading config file: {e}")
    
    # Read port and polling interval from config, with safe defaults
    port_number = config.get('prometheus_port', 8000)
    polling_interval = config.get('polling_interval_seconds', 60)

    # Allow command-line argument to override the port number from the config file
    if len(sys.argv) > 2:
        try:
            port_number = int(sys.argv[2])
        except ValueError:
            exit_with_error("Error: Port number must be an integer.")

    if "purifiers" not in config or not isinstance(config.get("purifiers"), list) or not config["purifiers"]:
        exit_with_error("No 'purifiers' list found in the JSON config file")

    purifiers = config["purifiers"]
    for p in purifiers:
        if not all(k in p for k in ["name", "ip", "token"]):
            print(f"Warning: Skipping a purifier entry due to missing 'name', 'ip', or 'token'.")
            continue
        print(f"Initializing purifier '{p['name']}' at {p['ip']}...")
        try:
            p["object"] = MiotDevice(ip=p['ip'], token=p['token'], mapping=MIOT_MAPPING)
        except exceptions.DeviceException as e:
            print(f"Warning: Could not connect to '{p['name']}' during initialization: {e}")
            p["object"] = None

    print(f"Starting Prometheus exporter on port {port_number}")
    print(f"Polling devices every {polling_interval} seconds")
    start_http_server(port_number)

    while True:
        for p in purifiers:
            if p.get("object") is None:
                continue

            purifier_name = p["name"]
            try:
                properties = p["object"].get_properties_for_mapping()
                status = {prop['did']: prop['value'] for prop in properties if prop.get('code') == 0}

                # Set all gauges based on the data received from the purifier
                if 'power' in status: power.labels(purifier_name).set(1 if status['power'] else 0)
                if 'mode' in status: mode.labels(purifier_name).set(status['mode'])
                if 'aqi' in status: aqi.labels(purifier_name).set(status['aqi'])
                if 'temperature' in status: temp.labels(purifier_name).set(status['temperature'])
                if 'humidity' in status: humidity.labels(purifier_name).set(status['humidity'])
                if 'fault' in status: fault.labels(purifier_name).set(status['fault'])
                if 'fan_speed_rpm' in status: fan_speed_rpm.labels(purifier_name).set(status['fan_speed_rpm'])
                if 'filter_life_remaining' in status: filter_life_remaining.labels(purifier_name).set(status['filter_life_remaining'])
                if 'filter_used_time' in status: filter_used_time.labels(purifier_name).set(status['filter_used_time'])
                if 'filter_left_time' in status: filter_left_time.labels(purifier_name).set(status['filter_left_time'])
                if 'favorite_level' in status: favorite_level.labels(purifier_name).set(status['favorite_level'])

            except exceptions.DeviceException as e:
                print(f"Error updating '{purifier_name}': {e}")
            except OSError as e:
                print(f"OS Error (network?) for '{purifier_name}': {e}")

        time.sleep(polling_interval)
