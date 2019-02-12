#python2.7 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. indoor_temperature_action.proto

from concurrent import futures
import time
import grpc
import indoor_temperature_action_pb2
import indoor_temperature_action_pb2_grpc
from xbos.services import mdal
from bw2python.client import Client
from xbos.services.hod import HodClient

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

# getting the utils file here
import os, sys
import xbos_services_utils2 as utils
import datetime
import pytz

def _get_raw_actions(building, zone, mdal_client, hod_client, start, end, window_size):
    """
    TODO how to deal with windows in which two different actions are performed in given zone.
    Note: GETS THE MAX ACTION IN GIVEN INTERVAL.
    :param building:
    :param zone:
    :param mdal_client:
    :param hod_client:
    :param start: datetime, timezone aware
    :param end: datetime, timezoneaware
    :param window_size: string with [s, m, h, d] calssified in the end. e.g. "1s" for one second.
    :return:
    """

    # following query is for the whole building.
    hod_thermostat_action_query = """SELECT ?zone ?uuid FROM %s WHERE { 
          ?tstat rdf:type brick:Thermostat .
          ?tstat bf:hasLocation/bf:isPartOf ?location_zone .
          ?location_zone rdf:type brick:HVAC_Zone .
          ?tstat bf:controls ?RTU .
          ?RTU rdf:type brick:RTU . 
          ?RTU bf:feeds ?zone. 
          ?zone rdf:type brick:HVAC_Zone . 
          ?tstat bf:hasPoint ?status_point .
          ?status_point rdf:type brick:Thermostat_Status .
          ?status_point bf:uuid ?uuid.
        };""" % building

    action_query_data = hod_client.do_query(hod_thermostat_action_query)["Rows"]
    action_zone_uuid = {row["?zone"]: row["?uuid"] for row in action_query_data}[zone]

    # get the data for the thermostats for queried zone.
    mdal_query = {
        'Composition': [action_zone_uuid],
        'Selectors': [mdal.MAX],
        'Time':     {'T0': utils.datetime_to_mdal_string(start),
                   'T1': utils.datetime_to_mdal_string(end),
                   'WindowSize': window_size,
                   'Aligned': True}}

    print(mdal_query)

    mdal_action_data = utils.get_mdal_data(mdal_client, mdal_query).squeeze()
    mdal_action_data.name = zone + "_raw_indoor_actions"
    return mdal_action_data, None


def _get_raw_indoor_temperatures(building, zone, mdal_client, hod_client, start, end, window_size):
    """

    :param building:
    :param zone:
    :param mdal_client:
    :param hod_client:
    :param start: datetime, timezone aware
    :param end: datetime, timezoneaware
    :param window_size:
    :return:
    """

    # following query is for the whole building.
    hod_temperature_query = """SELECT ?zone ?uuid FROM %s WHERE { 
          ?tstat rdf:type brick:Thermostat .
          ?tstat bf:hasLocation/bf:isPartOf ?location_zone .
          ?location_zone rdf:type brick:HVAC_Zone .
          ?tstat bf:controls ?RTU .
          ?RTU rdf:type brick:RTU . 
          ?RTU bf:feeds ?zone. 
          ?zone rdf:type brick:HVAC_Zone . 
          ?tstat bf:hasPoint ?thermostat_point .
          ?thermostat_point rdf:type brick:Temperature_Sensor .
          ?thermostat_point bf:uuid ?uuid.
        };""" % building



    temperature_query_data = hod_client.do_query(hod_temperature_query)["Rows"]
    temperature_zone_uuid = {row["?zone"]: row["?uuid"] for row in temperature_query_data}[zone]

    # get the data for the thermostats for each zone.
    mdal_query = {
        'Composition': [temperature_zone_uuid],
        'Selectors': [mdal.MEAN],
        'Time':     {'T0': utils.datetime_to_mdal_string(start),
                   'T1': utils.datetime_to_mdal_string(end),
                   'WindowSize': window_size,
                   'Aligned': True}}

    print(mdal_query)

    mdal_temperature_data = utils.get_mdal_data(mdal_client, mdal_query).squeeze()
    mdal_temperature_data.name = zone + "_raw_indoor_temperatures"
    return mdal_temperature_data, None


# TODO Make sure we don't include NONE values in the returned points.
def get_raw_indoor_temperatures(request, mdal_client, hod_client):
    """Returns temperatures for the given request or None."""
    print("received request:", request.building, request.zone, request.start, request.end, request.window)
    duration = utils.get_window_in_sec(request.window)

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

    start_datetime = datetime.datetime.utcfromtimestamp(
                                                        float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_datetime = datetime.datetime.utcfromtimestamp(float(request.end / 1e9)).replace(
                                                        tzinfo=pytz.utc)

    raw_indoor_temperature_data, err = _get_raw_indoor_temperatures(request.building, request.zone, mdal_client, hod_client,
                                                    start_datetime,
                                                    end_datetime,
                                                    request.window)
    temperatures = []

    if raw_indoor_temperature_data is None:
        return None, "No data received from database."

    for index, temp in raw_indoor_temperature_data.iteritems():
        temperatures.append(indoor_temperature_action_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp, unit=unit))

    return indoor_temperature_action_pb2.RawTemperatureReply(temperatures=temperatures), None


def get_raw_actions(request, mdal_client, hod_client):
    """Returns actions for the given request or None."""
    print("received request:", request.building, request.zone, request.start, request.end, request.window)
    duration = utils.get_window_in_sec(request.window)

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

    start_datetime = datetime.datetime.utcfromtimestamp(
                                                        float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_datetime = datetime.datetime.utcfromtimestamp(float(request.end / 1e9)).replace(
                                                        tzinfo=pytz.utc)


    raw_action_data, err = _get_raw_actions(request.building, request.zone, mdal_client, hod_client,
                                                    start_datetime,
                                                    end_datetime,
                                                    request.window)
    actions = []

    if raw_action_data is None:
        return None, "No data received from database."

    for index, action in raw_action_data.iteritems():
        actions.append(indoor_temperature_action_pb2.ActionPoint(time=int(index.timestamp() * 1e9), action=action)) # TOOD action being int will be a problem.

    return indoor_temperature_action_pb2.RawActionReply(actions=actions), None


class IndoorTemperatureActionServicer(indoor_temperature_action_pb2_grpc.IndoorTemperatureActionServicer):
    def __init__(self):
        self.bw_client = Client()
        self.bw_client.setEntityFromEnviron()
        self.bw_client.overrideAutoChainTo(True)
        self.hod_client = HodClient("xbos/hod", self.bw_client)
        self.mdal_client = mdal.MDALClient("xbos/mdal")

    def GetRawTemperatures(self, request, context):
        """A simple RPC.

        Sends the indoor temperature for a given HVAC zone, within a timeframe (start, end), and a requested window
        An error is returned if there are no temperatures for the given request
        """
        raw_temperatures, error = get_raw_indoor_temperatures(request, self.mdal_client, self.hod_client)
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
        raw_actions, error = get_raw_actions(request, self.mdal_client, self.hod_client)
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

