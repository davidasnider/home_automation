#!/usr/local/bin/python
"""
This script pulls data from a netatmo device and logs it to indigo as well
as influxdb.

"""
import time

import requests
from influxdb import InfluxDBClient

from home_automation import utilities

settings = utilities.Settings()

client_id = settings.netatmo_client_id
client_secret = settings.netatmo_client_secret
username = settings.email_to
password = settings.netatmo_password
device_id = settings.netatmo_device_id
influx_server = settings.statsd_server
indigo_username = settings.indigo_username
indigo_password = settings.indigo_password

data_start_time = int(time.time() * 1000)  # milliseconds
influx = InfluxDBClient(host=influx_server, port=8086, database="metrics")


# Create a function to convert celsius to fahrenheit
def convert_celsius_to_fahrenheit(celsius: float):
    """The US doesn't like easy math, give us hard to calculate stuff.

    Parameters
    ----------
    celsius : float
        The observed temperature in celsius

    Returns
    -------
    farenheit : float
        The converted temperature in farenheit
    """
    fahrenheit = 9.0 / 5.0 * celsius + 32
    return fahrenheit


# Let's get an access code
payload = {
    "grant_type": "password",
    "username": username,
    "password": password,
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "read_station",
}
try:
    response = requests.post("https://api.netatmo.com/oauth2/token", data=payload)
    response.raise_for_status()
    access_token = response.json()["access_token"]
    refresh_token = response.json()["refresh_token"]
    scope = response.json()["scope"]
except requests.exceptions.HTTPError as error:
    print(error.response.status_code, error.response.text)

# Let's get information from our station
params = {"access_token": access_token, "device_id": device_id}

try:
    response = requests.post(
        "https://api.netatmo.com/api/getstationsdata", params=params
    )
    response.raise_for_status()
    data = response.json()["body"]
except requests.exceptions.HTTPError as error:
    print(error.response.status_code, error.response.text)

# Setup our metrics array
metrics = []

# Get these additional measurements from Netatmo
additional_measurements = ["wifi_status", "battery_percent", "battery_vp", "rf_status"]

# Now lets get the info for our modules
for device in data["devices"]:
    device_name = device["module_name"]
    print(device_name, device["reachable"])
    for measurement in additional_measurements:
        if measurement in device.keys():
            metrics.append(
                {
                    "device": device_name,
                    "sensor": measurement,
                    "measurement": device[measurement],
                }
            )
            print(
                f"\tdevice: {device_name}, sensor: {measurement}, measurement: {device[measurement]}"
            )
    for device_data in device["data_type"]:
        # Let's make sure the dashboard data dictionary exists
        if "dashboard_data" in device.keys():
            metrics.append(
                {
                    "device": device_name,
                    "sensor": device_data,
                    "measurement": device["dashboard_data"][device_data],
                }
            )
            print(
                f"\tdevice: {device_name}, sensor: {device_data}, measurement: {device['dashboard_data'][device_data]}"
            )

for module in device["modules"]:
    module_name = module["module_name"]
    print(module_name, module["reachable"])
    for measurement in additional_measurements:
        if measurement in module.keys():
            metrics.append(
                {
                    "device": module_name,
                    "sensor": measurement,
                    "measurement": module[measurement],
                }
            )
    for module_data in module["data_type"]:
        if module_data == "Wind":
            additional_modules = [
                "GustAngle",
                "GustStrength",
                "WindAngle",
                "WindStrength",
            ]
            for additional_module in additional_modules:
                if "dashboard_data" in module.keys():
                    metrics.append(
                        {
                            "device": module_name,
                            "sensor": additional_module,
                            "measurement": module["dashboard_data"][additional_module],
                        }
                    )
                    print(
                        f"\tdevice: {module_name}, sensor: {additional_module}, measurement: {module['dashboard_data'][additional_module]}"
                    )
        else:
            if "dashboard_data" in module.keys():
                metrics.append(
                    {
                        "device": module_name,
                        "sensor": module_data,
                        "measurement": module["dashboard_data"][module_data],
                    }
                )
                print(
                    f"\tdevice: {module_name}, sensor: {module_data}, measurement: {module['dashboard_data'][module_data]}"
                )
        if module_data == "Rain":
            additional_modules = ["sum_rain_24"]
            for additional_module in additional_modules:
                if "dashboard_data" in module.keys():
                    metrics.append(
                        {
                            "device": module_name,
                            "sensor": additional_module,
                            "measurement": module["dashboard_data"][additional_module],
                        }
                    )
                    print(
                        f"\tdevice: {module_name}, sensor: {additional_module}, measurement: {module['dashboard_data'][additional_module]}"
                    )

# Fix all the celsius temperatures into Fahrenheit
for metric in metrics:
    if metric["sensor"] == "Temperature":
        metric["measurement"] = convert_celsius_to_fahrenheit(metric["measurement"])

# Now lets log it to InfluxDB
print("Logging to InfluxDB")
influx_data = []

for metric in metrics:
    influx_measure = (
        metric["sensor"] + ",device=" + metric["device"] + ",product=netatmo"
    )
    influx_data.append(
        "{sensor},device={device},product={product} value={value} {timestamp}".format(
            sensor=metric["sensor"],
            device=metric["device"],
            product="netatmo",
            value=metric["measurement"],
            timestamp=data_start_time,
        )
    )
    print(f"\t{influx_measure} with value: {metric['measurement']}")
influx.write_points(influx_data, time_precision="ms", batch_size=10000, protocol="line")

# Now lets log it to Indigo
print("Logging to Indigo")
for metric in metrics:
    if metric["sensor"] == "Temperature" and metric["device"] == "Outdoor":
        variableValue = "value=" + str(metric["measurement"])
        utilities.update_indigo_variable("Netatmo_Outside_Temp", variableValue)
        print(f"\tLogged {variableValue} to Netatmo_Outside_Temp")
    if metric["sensor"] == "Humidity" and metric["device"] == "Outdoor":
        variableValue = "value=" + str(metric["measurement"])
        utilities.update_indigo_variable("Netatmo_Outside_Humidity", variableValue)
        print(f"\tLogged {variableValue} to Netatmo_Outside_Humidity")
