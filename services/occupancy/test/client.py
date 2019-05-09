
from __future__ import print_function

import grpc
import time
import datetime
import occupancy_pb2
import occupancy_pb2_grpc

import calendar
import pytz

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    with grpc.insecure_channel('localhost:50054') as channel:
        stub = occupancy_pb2_grpc.OccupancyStub(channel)
        try:
            d_start = (datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=20))

            # d_start = datetime.datetime(year=2018, month=9, day=8, hour=21, minute=31, second=10).replace(tzinfo=pytz.utc)
            start = calendar.timegm(d_start.utctimetuple()) * 1e9

            end = calendar.timegm((datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(
                days=15)).utctimetuple()) * 1e9


            response = stub.GetOccupancy(occupancy_pb2.Request(building="avenal-animal-shelter", zone="HVAC_Zone_Shelter_Corridor", start=int(start),end=int(end),window="15m"))
            for point in response.occupancies:
                print("Point at: %s is occupancy: %f." % (time.ctime(int(point.time/1000000000.0)) + ' PST',
                                                                                                        point.occupancy))
        except grpc.RpcError as e:
            print(e)

if __name__ == '__main__':
    run()
