#!/usr/bin/python3

"""
Logs indigo metrics into the time series database
"""

import requests
import statsd
from requests.auth import HTTPDigestAuth

from home_automation import utilities

# Get the environment variables
settings = utilities.Settings()


indigo_devices = [
    {"name": "Computer Room Humidity", "metric": "humidity", "device": "computer_room"},
    {
        "name": "Computer Room Luminance",
        "metric": "luminance",
        "device": "computer_room",
    },
    {"name": "Computer Room Temperature", "metric": "temp", "device": "computer_room"},
    {
        "name": "Computer Room Ultraviolet",
        "metric": "ultraviolet",
        "device": "computer_room",
    },
    {
        "name": "Upstairs Hallway Humidity",
        "metric": "humidity",
        "device": "upstairs_hallway",
    },
    {
        "name": "Upstairs Hallway Luminance",
        "metric": "luminance",
        "device": "upstairs_hallway",
    },
    {
        "name": "Upstairs Hallway Temperature",
        "metric": "temp",
        "device": "upstairs_hallway",
    },
]


def getIndigoDevices():
    """
    Get the list of indigo devices

    Returns
    -------
    json
        All of the indigo devices
    """
    url = "http://blanc.thesniderpad.com:8000/devices.json"
    r = requests.get(
        url, auth=HTTPDigestAuth(settings.indigo_username, settings.indigo_password)
    )
    utilities.checkResponse(r)
    return r.json()


def getIndigoDevice(uri):
    """
    Get details for the passed indigo device

    Parameters
    ----------
    uri : httpURL
        the uri to access details for a device

    Returns
    -------
    json
        a json object with the details for the device
    """
    url = "http://blanc.thesniderpad.com:8000/devices/" + uri
    r = requests.get(
        url, auth=HTTPDigestAuth(settings.indigo_username, settings.indigo_password)
    )
    utilities.checkResponse(r)
    return r.json()


devices_json = getIndigoDevices()

for device in devices_json:
    for query_device in indigo_devices:
        if device["name"] == query_device["name"]:
            device_json = getIndigoDevice(device["restURL"])
            query_device["value"] = device_json["displayRawState"]

# Now lets log it to InfluxDB
statsd_connection = statsd.StatsClient(settings.statsd_server, 8125)

for device in indigo_devices:
    influx_measure = device["metric"] + ",device=" + device["device"]
    statsd_connection.gauge(influx_measure, device["value"])
    print(influx_measure, ": ", device["value"])
