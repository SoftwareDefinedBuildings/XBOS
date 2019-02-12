
from __future__ import print_function

import grpc
import time
import datetime
import schedules_pb2
import schedules_pb2_grpc

import calendar
import pytz

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    with grpc.insecure_channel('localhost:50055') as channel:
        stub = schedules_pb2_grpc.SchedulesStub(channel)
        try:
            d_start = (datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=20))

            # d_start = datetime.datetime(year=2018, month=9, day=8, hour=21, minute=31, second=10).replace(tzinfo=pytz.utc)
            start = calendar.timegm(d_start.utctimetuple()) * 1e9

            end = calendar.timegm((datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(
                days=15)).utctimetuple()) * 1e9


            comfortband_respones = stub.GetComfortband(schedules_pb2.Request(building="avenal-animal-shelter", zone="HVAC_Zone_Shelter_Corridor", start=int(start),end=int(end),window="15m", unit="F"))
            do_not_exceed_respones = stub.GetDoNotExceed(schedules_pb2.Request(building="avenal-animal-shelter", zone="HVAC_Zone_Shelter_Corridor", start=int(start),end=int(end),window="15m", unit="F"))

            for point in comfortband_respones.schedules:
                print("Point at: %s is t_low: %f and t_high: %f" % (time.ctime(int(point.time/1000000000.0)) + ' PST',
                                                                                                        point.temperature_low,
                                                                    point.temperature_high))
        except grpc.RpcError as e:
            print(e)



if __name__ == '__main__':
    run()
