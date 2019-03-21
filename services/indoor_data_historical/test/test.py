
from __future__ import print_function

import grpc
import time
import datetime

import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
import indoor_temperature_action_pb2
import indoor_temperature_action_pb2_grpc

import calendar
import pytz

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50060') as channel:
        stub = indoor_temperature_action_pb2_grpc.IndoorTemperatureActionStub(channel)
        try:
            start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            response = stub.GetRawTemperatures(indoor_temperature_action_pb2.Request(building="ciee", zone="HVAC_Zone_Eastzone", start=start,end=end,window="1m"))
            for temperature in response.temperatures:
                print("Temp at: %s is: %.2f %s" % (time.ctime(int(temperature.time/1000000000.0)) + ' PST', temperature.temperature, temperature.unit))
        except grpc.RpcError as e:
            print(e)

    with grpc.insecure_channel('localhost:50060') as channel:
        stub = indoor_temperature_action_pb2_grpc.IndoorTemperatureActionStub(channel)
        try:
            start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            end =  int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            response = stub.GetRawActions(indoor_temperature_action_pb2.Request(building="ciee", zone="HVAC_Zone_Eastzone", start=start,end=end,window="1m"))
            for action in response.actions:
                print("Action at: %s is: %f" % (time.ctime(int(action.time/1000000000.0)) + ' PST', action.action))
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
