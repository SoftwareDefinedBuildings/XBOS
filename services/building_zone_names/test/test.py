from __future__ import print_function

import grpc

from pathlib import Path
import sys
sys.path.append(str(Path.cwd().parent))
import building_zone_names_pb2
import building_zone_names_pb2_grpc

import os
HOST_ADDRESS = os.environ["BUILDING_ZONE_NAMES_HOST_ADDRESS"]


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    channel = grpc.insecure_channel(HOST_ADDRESS)
    stub = building_zone_names_pb2_grpc.BuildingZoneNamesStub(channel)

    # get all building names
    building_names = stub.GetBuildings(building_zone_names_pb2.BuildingRequest())

    # for all available buildings, get the zones
    for bldg in building_names.names:
        print("Getting Building: ", bldg.name)
        curr_zones = stub.GetZones(building_zone_names_pb2.ZoneRequest(building=bldg.name))


if __name__ == '__main__':
    run()
