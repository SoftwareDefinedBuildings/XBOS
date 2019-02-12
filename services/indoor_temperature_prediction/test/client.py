
from __future__ import print_function

import grpc
import time
import datetime
import thermal_model_pb2
import thermal_model_pb2_grpc

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
    with grpc.insecure_channel('localhost:50053') as channel:
        stub = thermal_model_pb2_grpc.ThermalModelStub(channel)
        try:
            # response = stub.GetPrice(price_pb2.PriceRequest(utility="PGE",tariff="PGEA10",price_type="energy",start=int((time.time())*1000000000.0),end=int((time.time()+3600*2)*1000000000.0),window="15m"))
            start = int(time.mktime(datetime.datetime.strptime("17/09/2018 6:30:00", "%d/%m/%Y %H:%M:%S").timetuple())*1000000000)
            response = stub.GetPrediction(thermal_model_pb2.PredictionRequest(building="ciee",
                                                                              zone="HVAC_Zone_Northzone",
                                                                              current_time=start,
                                                                              indoor_temperature=70,
                                                                              outside_temperature=80,
                                                                              action=0,
                                                                              zone_temperatures={
                                                                                  "HVAC_Zone_Eastzone": 75,
                                                                                  "HVAC_Zone_Southzone": 60,
                                                                                  "HVAC_Zone_Centralzone": 80
                                                                              },
                                                                                temperature_unit="F",
                                                                              occupancy=1))
            print("Temp at: %s is: %.2f %s" % (time.ctime(int(response.time/1000000000.0)) + ' PST', response.temperature, response.unit))
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
