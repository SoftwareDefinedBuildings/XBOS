# TODO test what happens with Nan values.

from concurrent import futures
import time
import grpc
import outdoor_temperature_historical_pb2
import outdoor_temperature_historical_pb2_grpc
from xbos.services import mdal
from bw2python.client import Client
from xbos.services.hod import HodClient

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


# getting the utils file here
import os, sys
import xbos_services_utils2 as utils
import datetime
import pytz
import numpy as np


def _preprocess_mdal_outside_data(outside_data):
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
            lambda t: np.nan if t == 32 else t)  # TODO this only works for fahrenheit now.

    # Note: Assuming same index for all weather station data returned by mdal
    outside_data = outside_data.mean(axis=1)

    outside_data = outside_data.interpolate("time")

    return outside_data, None


def _get_mdal_outside_data(building, start, end, interval, mdal_client):
    """Get outside temperature.
    :param start: datetime timezone aware
    :param end: datetime timezone aware
    :param interval: int:seconds. [Not used at the moment because of MDAL issue.]
    :param mdal_client: Client to get data.
    :return ({uuid: (pd.df) (col: "t_out) outside_data})  outside temperature has freq of 15 min and
    pd.df columns["tin", "action"] has freq of window_size. """

    outside_temperature_query = """SELECT ?uuid FROM %s WHERE {
                                ?weather_station rdf:type brick:Weather_Temperature_Sensor.
                                ?weather_station bf:uuid ?uuid.
                                };""" % building

    # TODO for now taking all weather stations and preprocessing it. Should be determined based on metadata.
    # Get data from MDAL
    mdal_query = {
        'Composition': ["weather_stations"],
        'Selectors': [mdal.MEAN],
        'Variables': [{"Name": "weather_stations",
                       "Definition": outside_temperature_query,
                       "Units": "F"},],
        'Time': {'T0': utils.datetime_to_mdal_string(start),
                   'T1': utils.datetime_to_mdal_string(end),
                   'WindowSize': str(int(interval)) + 's',
                   'Aligned': True}}
    try:
        mdal_outside_data = utils.get_mdal_data(mdal_client, mdal_query)
    except:
        return None, "could not fetch data from mdal with query: %s" % mdal_query

    if mdal_outside_data is None:
        return None, "did not fetch data from mdal with query: %s" % mdal_query

    return mdal_outside_data, None


def _get_temperature(building, start, end, interval, mdal_client):

    raw_outside_data, err = _get_mdal_outside_data(building, start, end, interval, mdal_client)
    if raw_outside_data is None:
        return None, err

    preprocessed_data, err = _preprocess_mdal_outside_data(raw_outside_data)

    return preprocessed_data, err


def get_temperature(request, mdal_client):
    """Returns temperatures for a given request or None.
    Guarantees that no Nan values in returned data exist."""
    print("received request:", request.building, request.start, request.end, request.window)
    duration = utils.get_window_in_sec(request.window)

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

    d_start = datetime.datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    final_data, err = _get_temperature(request.building, d_start, d_end, duration, mdal_client)
    if final_data is None:
        return None, err

    temperatures = []

    for index, temp in final_data.iteritems():
        temperatures.append(outdoor_temperature_historical_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp, unit=unit))

    return outdoor_temperature_historical_pb2.TemperatureReply(temperatures=temperatures), None

class OutdoorTemperatureServicer(outdoor_temperature_historical_pb2_grpc.OutdoorTemperatureServicer):
    def __init__(self):
        self.bw_client = Client()
        self.bw_client.setEntityFromEnviron()
        self.bw_client.overrideAutoChainTo(True)
        self.hod_client = HodClient("xbos/hod", self.bw_client)
        self.mdal_client = mdal.MDALClient("xbos/mdal")

    def GetTemperature(self, request, context):
        temperatures,error = get_temperature(request, self.mdal_client)
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
