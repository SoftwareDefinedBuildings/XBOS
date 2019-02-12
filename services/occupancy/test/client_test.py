from __future__ import print_function

import grpc
import time
import datetime
import occupancy_pb2
import occupancy_pb2_grpc

import calendar
import pytz

# getting the utils file here
import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
xbos_services_path = os.path.dirname(os.path.dirname(FILE_PATH))
sys.path.append(xbos_services_path)
import utils

def test_occ():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    all_bldgs = utils.get_buildings()

    channel = grpc.insecure_channel('localhost:50054')
    stub = occupancy_pb2_grpc.OccupancyStub(channel)


    for bldg in all_bldgs:
        # case 1, Test from now into future
        print("Building: %s" % bldg)
        for zone in utils.get_zones(bldg):
            s_time = time.time()
            print("Zone: %s" % zone)
            try:
                d_start = datetime.datetime(2018, 01, 01).replace(tzinfo=pytz.utc)

                start = calendar.timegm(d_start.utctimetuple()) * 1e9

                end = calendar.timegm((d_start.replace(tzinfo=pytz.utc) + datetime.timedelta(
                    days=10)).utctimetuple()) * 1e9


                response = stub.GetOccupancy(occupancy_pb2.Request(building=bldg, zone=zone, start=int(start),end=int(end),window="15m"))
                for point in response.occupancies:
                    print("Point at: %s is occupancy: %f." % (time.ctime(int(point.time/1000000000.0)) + ' PST',
                                                                                                            point.occupancy))
            except grpc.RpcError as e:
                       print(e)
            print("Took: %f seconds" % (time.time() - s_time))
        print("")
    print("")

if __name__ == '__main__':
    test_occ()
