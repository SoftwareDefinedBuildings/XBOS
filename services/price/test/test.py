from __future__ import print_function

import grpc
import time
import datetime

from pathlib import Path
import sys
sys.path.append(str(Path.cwd().parent))
import price_pb2
import price_pb2_grpc


import os
PRICE_HOST_ADDRESS = os.environ["PRICE_HOST_ADDRESS"]

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel(PRICE_HOST_ADDRESS) as channel:
        stub = price_pb2_grpc.PriceStub(channel)
        try:
            # response = stub.GetPrice(price_pb2.PriceRequest(utility="PGE",tariff="PGEA10",price_type="energy",start=int((time.time())*1000000000.0),end=int((time.time()+3600*2)*1000000000.0),window="15m"))
            start = int(time.mktime(datetime.datetime.strptime("26/09/2018 6:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            end =  int(time.mktime(datetime.datetime.strptime("26/09/2018 10:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            response = stub.GetPrice(price_pb2.PriceRequest(utility="PGE",tariff="PGEA10",price_type="energy",start=start,end=end,window="29m"))
            for price in response.prices:
                # print("Price at: %s is: %.2f %s" % (time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(int(price.time/1000000000.0))) + ' UTC', price.price, price.unit))
                print("Price at: %s is: %.2f %s for %s " % (time.ctime(int(price.time/1000000000.0)) + ' PST', price.price, price.unit,price.window))
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
