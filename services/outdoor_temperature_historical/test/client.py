
from __future__ import print_function

import grpc
import time
import datetime

from pathlib import Path
import sys
sys.path.append(str(Path.cwd().parent))
import outdoor_temperature_historical_pb2
import outdoor_temperature_historical_pb2_grpc

import pytz

import calendar


_EPOCH = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)

def timestamp(self):
        "Return POSIX timestamp as float"
        if self.tzinfo is None:
            return time.mktime((self.year, self.month, self.day,
                                 self.hour, self.minute, self.second,
                                 -1, -1, -1)) + self.microsecond / 1e6
        else:
            return (self - _EPOCH).total_seconds()

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50058') as channel:
        stub = outdoor_temperature_historical_pb2_grpc.OutdoorTemperatureStub(channel)
        try:

            bldg = "ciee"

            d_start = pytz.utc.localize(datetime.datetime(2018, 1, 1, minute=2))
            d_end = d_start + datetime.timedelta(days=2)

            start = int(calendar.timegm(d_start.utctimetuple()) * 1e9)
            end = int(calendar.timegm(d_end.utctimetuple()) * 1e9)


            response = stub.GetTemperature(outdoor_temperature_historical_pb2.TemperatureRequest(building=bldg,start=start,end=end,window="15m"))
            for temperature in response.temperatures:
                print("Temp at: %s is: %.2f %s" % (time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(int(temperature.time/1000000000.0))) + ' UTC', temperature.temperature, temperature.unit))
                # print("Temp at: %s is: %.2f %s" % (time.ctime(int(temperature.time/1000000000.0)) + ' PST', temperature.temperature, temperature.unit))
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
