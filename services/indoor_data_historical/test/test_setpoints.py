from __future__ import print_function

import grpc
import time
import datetime
import pytz
import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
import indoor_temperature_action_pb2
import indoor_temperature_action_pb2_grpc

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50060') as channel:
        stub = indoor_temperature_action_pb2_grpc.IndoorTemperatureActionStub(channel)
        try:
            end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
            start = end - datetime.timedelta(days=1)
            start = int(time.mktime(start.timetuple())*1e9)
            end =  int(time.mktime(end.timetuple())*1e9)

            temperature_bands_response = stub.GetRawTemperatureBands(indoor_temperature_action_pb2.Request(building="ciee", zone="hvac_zone_eastzone", start=start,end=end,window="1h"))
            heating_setpoints = temperature_bands_response.heating_setpoints
            cooling_setpoints = temperature_bands_response.cooling_setpoints
            print(temperature_bands_response)

        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
     run()
