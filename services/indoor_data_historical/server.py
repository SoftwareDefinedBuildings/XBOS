#python2.7 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. indoor_temperature_action.proto

from concurrent import futures
import time
import grpc
import pymortar
import indoor_temperature_action_pb2
import indoor_temperature_action_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

import os, sys
from datetime import datetime
from rfc3339 import rfc3339
import pytz

def _get_raw_actions(building, zone, pymortar_client, start, end, window_size):
    """
    TODO how to deal with windows in which two different actions are performed in given zone.
    Note: GETS THE MAX ACTION IN GIVEN INTERVAL.
    :param building:
    :param zone:
    :param pymortar_client:
    :param start: datetime, timezone aware, rfc3339
    :param end: datetime, timezone aware, rfc3339
    :param window_size: string with [s, m, h, d] classified in the end. e.g. "1s" for one second.
    :return:
    """
    thermostat_action_query = """SELECT ?tstat ?zone ?status_point WHERE { 
            ?tstat rdf:type brick:Thermostat .
            ?tstat bf:controls/bf:feeds ?zone .
            ?tstat bf:hasPoint ?status_point .
            ?status_point rdf:type brick:Thermostat_Status .
        };"""

    # resp = pymortar_client.qualify([thermostat_action_query]) Needed to get list of all sites

    thermostat_action_view = pymortar.View(
        name="thermostat_action_view",
        sites=[building],
        definition=thermostat_action_query,
    )

    thermostat_action_stream = pymortar.DataFrame(
        name="thermostat_action",
        aggregation=pymortar.MAX,
        window=window_size,
        timeseries=[
            pymortar.Timeseries(
                view="thermostat_action_view",
                dataVars=["?status_point"],
            )
        ]
    )

    request = pymortar.FetchRequest(
        sites=[building],
        views=[
            thermostat_action_view
        ],
        dataFrames=[
            thermostat_action_stream
        ],
        time=pymortar.TimeParams(
            start=rfc3339(start),
            end=rfc3339(end),
        )
    )

    thermostat_action_data = pymortar_client.fetch(request)["thermostat_action"]

    if thermostat_action_data is None:
        return None, "did not fetch data from pymortar with query: %s" % thermostat_action_query

    return thermostat_action_data, None

def _get_raw_indoor_temperatures(building, zone, pymortar_client, start, end, window_size):
    """

    :param building:
    :param zone:
    :param pymortar_client:
    :param start: datetime, timezone aware, rfc3339
    :param end: datetime, timezone aware, rfc3339
    :param window_size:
    :return:
    """
    temperature_query = """SELECT ?tstat ?temp WHERE {
                ?tstat rdf:type brick:Thermostat .
                ?tstat bf:controls/bf:feeds %s .
                ?tstat bf:hasPoint ?temp .
                ?temp  rdf:type brick:Temperature_Sensor  .
            };""" % zone

    # resp = pymortar_client.qualify([temperature_query]) Needed to get list of all sites

    temperature_view = pymortar.View(
        name="temperature_view",
        sites=[building],
        definition=temperature_query,
    )

    temperature_stream = pymortar.DataFrame(
        name="temperature",
        aggregation=pymortar.MEAN,
        window=window_size,
        timeseries=[
            pymortar.Timeseries(
                view="temperature_view",
                dataVars=["?temp"],
            )
        ]
    )

    request = pymortar.FetchRequest(
        sites=[building],
        views=[
            temperature_view
        ],
        dataFrames=[
            temperature_stream
        ],
        time=pymortar.TimeParams(
            start=rfc3339(start),
            end=rfc3339(end),
        )
    )

    temperature_data = pymortar_client.fetch(request)["temperature"]

    if temperature_data is None:
        return None, "did not fetch data from pymortar with query: %s" % temperature_query

    return temperature_data, None


# TODO Make sure we don't include NONE values in the returned points.
def get_raw_indoor_temperatures(request, pymortar_client):
    """Returns temperatures for the given request or None."""
    print("received request:", request.building, request.zone, request.start, request.end, request.window)
    duration = get_window_in_sec(request.window)

    unit = "F" # we will keep the outside temperature in fahrenheit for now.

    request_length = [len(request.building), len(request.zone), request.start, request.end,
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

    start_datetime = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_datetime = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(
                                                        tzinfo=pytz.utc)

    raw_indoor_temperature_data, err = _get_raw_indoor_temperatures(request.building, request.zone, pymortar_client,
                                                    start_datetime,
                                                    end_datetime,
                                                    request.window)
    temperatures = []

    if raw_indoor_temperature_data is None:
        return None, "No data received from database."

    for index, temp in raw_indoor_temperature_data.iteritems():
        temperatures.append(indoor_temperature_action_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp, unit=unit))

    return indoor_temperature_action_pb2.RawTemperatureReply(temperatures=temperatures), None


def get_raw_actions(request, pymortar_client):
    """Returns actions for the given request or None."""
    print("received request:", request.building, request.zone, request.start, request.end, request.window)
    duration = get_window_in_sec(request.window)

    request_length = [len(request.building), len(request.zone), request.start, request.end,
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

    start_datetime = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_datetime = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(
                                                        tzinfo=pytz.utc)


    raw_action_data, err = _get_raw_actions(request.building, request.zone, pymortar_client,
                                                    start_datetime,
                                                    end_datetime,
                                                    request.window)
    actions = []

    if raw_action_data is None:
        return None, "No data received from database."

    for index, action in raw_action_data.iteritems():
        actions.append(indoor_temperature_action_pb2.ActionPoint(time=int(index.timestamp() * 1e9), action=action)) # TOOD action being int will be a problem.

    return indoor_temperature_action_pb2.RawActionReply(actions=actions), None

def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
       Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0

class IndoorTemperatureActionServicer(indoor_temperature_action_pb2_grpc.IndoorTemperatureActionServicer):
    def __init__(self):
        self.pymortar_client = pymortar.Client()

    def GetRawTemperatures(self, request, context):
        """A simple RPC.

        Sends the indoor temperature for a given HVAC zone, within a timeframe (start, end), and a requested window
        An error is returned if there are no temperatures for the given request
        """
        raw_temperatures, error = get_raw_indoor_temperatures(request, self.pymortar_client)
        if raw_temperatures is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return indoor_temperature_action_pb2.RawTemperatureReply()
        else:
            return raw_temperatures

    def GetRawActions(self, request, context):
        """A simple RPC.

         Sends the indoor action for a given HVAC Zone, within a timeframe (start, end), and a requested window
         An error is returned if there are no actions for the given request
         """
        raw_actions, error = get_raw_actions(request, self.pymortar_client)
        if raw_actions is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return indoor_temperature_action_pb2.RawActionReply()
        else:
            return raw_actions


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    indoor_temperature_action_pb2_grpc.add_IndoorTemperatureActionServicer_to_server(IndoorTemperatureActionServicer(), server)
    server.add_insecure_port('[::]:50060')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()