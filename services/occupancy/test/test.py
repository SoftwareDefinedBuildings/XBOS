from __future__ import print_function

import grpc
import time
import datetime

from pathlib import Path
import sys
sys.path.append(str(Path.cwd().parent))
import occupancy_pb2
import occupancy_pb2_grpc

import pytz

import xbos_services_utils3 as utils

import os
OCCUPANCY_HOST_ADDRESS = os.environ["OCCUPANCY_HOST_ADDRESS"]


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    all_bldgs = utils.get_buildings()

    channel = grpc.insecure_channel(OCCUPANCY_HOST_ADDRESS)
    stub = occupancy_pb2_grpc.OccupancyStub(channel)


    for bldg in all_bldgs:
        # case 1, Test from now into future
        print("Building: %s" % bldg)
        for zone in utils.get_zones(bldg):
            s_time = time.time()
            print("Zone: %s" % zone)
            if "Shelter" not in zone:
                print("BREAK")
                break
            try:

                end = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) #+ datetime.timedelta(days=1)
                end_unix = int(end.timestamp() * 1e9)
                start = end - datetime.timedelta(days=1)
                start_unix = int(start.timestamp() * 1e9)

                window = "5m"

                response = stub.GetOccupancy(occupancy_pb2.Request(building=bldg, zone=zone, start=start_unix,end=end_unix,window=window))
                # for point in response.occupancies:
                #     print("Point at: %s is occupancy: %f." % (time.ctime(int(point.time/1000000000.0)) + ' PST',
                #                                                                                             point.occupancy))
            except grpc.RpcError as e:
                       print(e)
            print("Took: %f seconds" % (time.time() - s_time))
        print("")
    print("")


if __name__ == '__main__':
    run()
