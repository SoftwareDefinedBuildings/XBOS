import pandas as pd
import pytz
import requests
import xml.etree.ElementTree as ET

from datetime import datetime, timezone, timedelta

_INPUT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
_PELICAN_API_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
_pelican_time = pytz.timezone('US/Pacific')

_mode_name_mappings = {
    "Off": 0,
    "Heat": 1,
    "Cool": 2,
    "Auto": 3,
}

_state_mappings = {
    "Off": 0,
    "Heat-Stage1": 1,
    "Heat-Stage2": 4,
    "Cool-Stage1": 2,
    "Cool-Stage2": 5,
}

def _lookupHeatNeedsFan(site, username, password, tstat_name):
    base_url = "https://{}.officeclimatecontrol.net/api.cgi".format(site)
    therm_request_params = {
        "username": username,
        "password": password,
        "request": "get",
        "object": "Thermostat",
        "selection": "name:{};".format(tstat_name),
        "value": "HeatNeedsFan",
    }

    r = requests.get(base_url, params=therm_request_params)
    if r.status_code != requests.codes.ok:
        print("Thermostat response has bad status {}".format(r.status_code))
        return None
    response = ET.fromstring(r.text)
    if response.find("success").text != "1":
        print("Error retrieving thermostat information: " + response.find("message").text)
        return None
    return response.find("Thermostat/HeatNeedsFan").text

def _lookupHistoricalData(site, username, password, tstat_name, start, end):
    assert end - start <= timedelta(days=30)
    start_repr = start.strftime(_PELICAN_API_TIME_FORMAT)
    end_repr = end.strftime(_PELICAN_API_TIME_FORMAT)

    base_url = "https://{}.officeclimatecontrol.net/api.cgi".format(site)
    history_request_params = {
        "username": username,
        "password": password,
        "request": "get",
        "object": "ThermostatHistory",
        "selection": "name:{};startDateTime:{};endDateTime:{};".format(tstat_name, start_repr, end_repr),
        "value": "temperature;humidity;heatSetting;coolSetting;setBy;fan;system;runStatus;timestamp;",
    }

    r = requests.get(base_url, params=history_request_params)
    if r.status_code != requests.codes.ok:
        print("Thermostat history response has bad status {}".format(r.status_code))
        return None
    response = ET.fromstring(r.text)
    if response.find("success").text != "1":
        print("Error retrieving thermostat history: " + response.find("message").text)
        return None
    return ET.fromstring(r.text).findall("ThermostatHistory/History")

def fillPelicanHole(site, username, password, tstat_name, start_time, end_time):
    """Fill a hole in a Pelican thermostat's data stream.

    Arguments:
        site -- The thermostat's Pelican site name
        username -- The Pelican username for the site
        password -- The Pelican password for the site
        tstat_name -- The name of the thermostat, as identified by Pelican
        start_time -- The start of the data hole in UTC, e.g. "2018-01-29 15:00:00"
        end_time -- The end of the data hole in UTC, e.g. "2018-01-29 16:00:00"

    Returns:
        A Pandas dataframe with historical Pelican data that falls between the
        specified start and end times.

    Note that this function assumes the Pelican thermostat's local time zone is
    US/Pacific. It will properly handle PST vs. PDT.
    """

    start = datetime.strptime(start_time, _INPUT_TIME_FORMAT).replace(tzinfo=pytz.utc).astimezone(_pelican_time)
    end = datetime.strptime(end_time, _INPUT_TIME_FORMAT).replace(tzinfo=pytz.utc).astimezone(_pelican_time)

    heat_needs_fan = _lookupHeatNeedsFan(site, username, password, tstat_name)
    if heat_needs_fan is None:
        return None

    # Pelican's API only allows a query covering a time range of up to 1 month
    # So we may need run multiple requests for historical data
    history_blocks = []
    while start < end:
        block_start = start
        block_end = min(start + timedelta(days=30), end)
        blocks = _lookupHistoricalData(site, username, password, tstat_name, block_start, block_end)
        if blocks is None:
            return None
        history_blocks.extend(blocks)
        start += timedelta(days=30, minutes=1)

    output_rows = []
    for block in history_blocks:
        runStatus = block.find("runStatus").text
        if runStatus.startswith("Heat"):
            fanState = (heatNeedsFan == "Yes")
        else:
            fanState = (runStatus != "Off")

        api_time = datetime.strptime(block.find("timestamp").text, "%Y-%m-%dT%H:%M").replace(tzinfo=_pelican_time)
        # Need to convert seconds to nanoseconds
        timestamp = int(api_time.timestamp() * 10**9)

        output_rows.append({
            "temperature": float(block.find("temperature").text),
            "relative_humidity": float(block.find("humidity").text),
            "heating_setpoint": float(block.find("heatSetting").text),
            "cooling_setpoint": float(block.find("coolSetting").text),
            # Driver explicitly uses "Schedule" field, but we don't have this in history
            "override": block.find("setBy").text != "Schedule",
            "fan": fanState,
            "mode": _mode_name_mappings[block.find("system").text],
            "state": _state_mappings.get(runStatus, 0),
            "time": timestamp,
        })
    return pd.DataFrame(output_rows)
