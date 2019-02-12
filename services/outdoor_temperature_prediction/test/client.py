
from __future__ import print_function

import grpc
import time
import datetime
import outdoor_temperature_prediction_pb2
import outdoor_temperature_prediction_pb2_grpc

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50059') as channel:
        stub = outdoor_temperature_prediction_pb2_grpc.OutdoorTemperatureStub(channel)
        try:
            # response = stub.GetPrice(price_pb2.PriceRequest(utility="PGE",tariff="PGEA10",price_type="energy",start=int((time.time())*1000000000.0),end=int((time.time()+3600*2)*1000000000.0),window="15m"))
            start = int(time.mktime(datetime.datetime.strptime("2/02/2019 2:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            end =  int(time.mktime(datetime.datetime.strptime("2/02/2019 22:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            response = stub.GetTemperature(outdoor_temperature_prediction_pb2.TemperatureRequest(building="ciee",start=start,end=end,window="1h"))
            for temperature in response.temperatures:
                # print("Price at: %s is: %.2f %s" % (time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(int(price.time/1000000000.0))) + ' UTC', price.price, price.unit))
                print("Temp at: %s is: %.2f %s" % (time.ctime(int(temperature.time/1e9)) + ' PST', temperature.temperature, temperature.unit))
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
