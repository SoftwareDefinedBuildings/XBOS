
from __future__ import print_function

import grpc
import time
import datetime
import indoor_temperature_prediction_pb2
import indoor_temperature_prediction_pb2_grpc
import pytz

#   string building = 1;
#   string zone = 2;
#
#   // The start time in Unixnanoseconds
#   int64 current_time = 3;
#
#   int64 action = 4;
#
#
#   double indoor_temperature = 5;
#   double outside_temperature = 6;
#   map<string, double> zone_temperatures = 7;
#   string temperature_unit = 8;
#
#   double occupancy = 9;

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50060') as channel:
        stub = indoor_temperature_prediction_pb2_grpc.IndoorTemperaturePredictionStub(channel)
        try:

            now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)  # + datetime.timedelta(days=1)

            now_unix = int(now.timestamp() * 1e9)

            response = stub.GetSecondOrderPrediction(indoor_temperature_prediction_pb2.SecondOrderPredictionRequest(building="ciee",
                                                                  zone="HVAC_Zone_Northzone",
                                                                  current_time=now_unix,
                                                                  indoor_temperature=70,
                                                                  outside_temperature=80,
                                                                  previous_indoor_temperature=70,
                                                                  action=0,
                                                                  other_zone_temperatures={
                                                                      "HVAC_Zone_Eastzone": 75,
                                                                      "HVAC_Zone_Southzone": 60,
                                                                      "HVAC_Zone_Centralzone": 80
                                                                  },
                                                                    temperature_unit="F",))

            print("Temp at: %s is: %.2f %s" % (time.ctime(int(response.time/1000000000.0)) + ' PST', response.temperature, response.unit))
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
