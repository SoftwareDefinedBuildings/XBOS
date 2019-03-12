# TODO test what happens with Nan values.

from concurrent import futures
import time
import grpc
import pymortar
import outdoor_temperature_historical_pb2
import outdoor_temperature_historical_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

import os, sys
from datetime import datetime
from rfc3339 import rfc3339
from numpy import nan
import pytz

# TODO Change this function to fit pymortar data instead of mdal
def _preprocess_pymortar_outside_data(outside_data):
    """
    Fixes mdal bug.
    Interpolating is justified by:
    - Introducing limited inaccuracies: Data contains at most a few hours of consecutive nan data.
    - Is necessary: Due to MDAL, at a windowSize of less than 15 min, nan values appear between real values.
    :param outside_data: pd.df with column for each weather station.
    :return: pd.Series
    """

    # Due to MDAL bug, nan values were stored as 32.
    if len(outside_data) == 1:
        print("WARNING: Only one weather station for selected region. We need to replace 32 values with Nan due to "
              "past inconsistencies, but not enough data to compensate for the lost data by taking mean.")
    outside_data = outside_data.applymap(
            lambda t: nan if t == 32 else t)  # TODO this only works for fahrenheit now.

    # Note: Assuming same index for all weather station data returned by mdal
    outside_data = outside_data.mean(axis=1)

    outside_data = outside_data.interpolate("time")

    return outside_data, None


def _get_pymortar_outside_data(building, start, end, interval, pymortar_client):
    """Get outside temperature.
    :param start: datetime, timezone aware, rfc3339
    :param end: datetime, timezone aware, rfc3339
    :param interval: int:seconds.
    :param pymortar_client: Client to get data.
    :return ({uuid: (pd.df) (col: "t_out) outside_data})  outside temperature has freq of 15 min and
    pd.df columns["tin", "action"] has freq of window_size. """

    outside_temperature_query = """SELECT ?temp WHERE {
        ?temp rdf:type brick:Weather_Temperature_Sensor .
    };"""

    # resp = pymortar_client.qualify([outside_temperature_query]) Needed to get list of all sites

    weather_stations_view = pymortar.View(
        name="weather_stations_view",
        sites=[building],
        definition=outside_temperature_query,
    )

    weather_stations_stream = pymortar.DataFrame(
        name="weather_stations",
        aggregation=pymortar.MEAN,
        window=str(int(interval)) + 's',
        timeseries=[
            pymortar.Timeseries(
                view="weather_stations_view",
                dataVars=["?temp"],
            )
        ]
    )

    weather_stations_time_params = pymortar.TimeParams(
        start=start,
        end=end,
    )

    request = pymortar.FetchRequest(
        sites=[building],
        views=[
            weather_stations_view
        ],
        dataFrames=[
            weather_stations_stream
        ],
        time=weather_stations_time_params
    )

    outside_temperature_data = pymortar_client.fetch(request)

    if outside_temperature_data is None:
        return None, "did not fetch data from pymortar with query: %s" % outside_temperature_query

    return outside_temperature_data, None


def _get_temperature(building, start, end, interval, pymortar_client):

    raw_outside_data, err = _get_pymortar_outside_data(building, start, end, interval, pymortar_client)
    if raw_outside_data is None:
        return None, err

    preprocessed_data, err = _preprocess_pymortar_outside_data(raw_outside_data)

    return preprocessed_data, err


def get_temperature(request, pymortar_client):
    """Returns temperatures for a given request or None.
    Guarantees that no Nan values in returned data exist."""
    print("received request:", request.building, request.start, request.end, request.window)
    duration = get_window_in_sec(request.window)

    unit = "F" # we will keep the outside temperature in fahrenheit for now.

    request_length = [len(request.building), request.start, request.end,
                      duration]
    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if request.end > int(time.time() * 1e9):
        return None, "invalid request, end date is in the future."
    if request.start >= request.end:
        return None, "invalid request, start date is after end date."
    if request.start < 0 or request.end < 0:
        return None, "invalid request, negative dates"
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"

    d_start = rfc3339(datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc))
    d_end = rfc3339(datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc))

    final_data, err = _get_temperature(request.building, d_start, d_end, duration, pymortar_client)
    if final_data is None:
        return None, err

    temperatures = []

    for index, temp in final_data.iteritems():
        temperatures.append(outdoor_temperature_historical_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp, unit=unit))

    return outdoor_temperature_historical_pb2.TemperatureReply(temperatures=temperatures), None

def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
       Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0

class OutdoorTemperatureServicer(outdoor_temperature_historical_pb2_grpc.OutdoorTemperatureServicer):
    def __init__(self):
        self.pymortar_client = pymortar.Client()

    def GetTemperature(self, request, context):
        temperatures,error = get_temperature(request, self.pymortar_client)
        if temperatures is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return outdoor_temperature_historical_pb2.TemperatureReply()
        else:
            return temperatures


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    outdoor_temperature_historical_pb2_grpc.add_OutdoorTemperatureServicer_to_server(OutdoorTemperatureServicer(), server)
    server.add_insecure_port('[::]:50058')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
