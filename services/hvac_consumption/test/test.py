from __future__ import print_function

import grpc
import time
import datetime

from pathlib import Path
import sys
sys.path.append(str(Path.cwd().parent))
import hvac_consumption_pb2
import hvac_consumption_pb2_grpc

import calendar
import pytz

import xbos_services_utils3 as utils

import os
HOST_ADDRESS = os.environ["HVAC_CONSUMPTION_HOST_ADDRESS"]


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    all_bldgs = utils.get_buildings()

    channel = grpc.insecure_channel(HOST_ADDRESS)
    stub = hvac_consumption_pb2_grpc.ConsumptionHVACStub(channel)

    for bldg in all_bldgs:
        # case 1, Test from now into future
        print("Building: %s" % bldg)
        for zone in utils.get_zones(bldg):
            s_time = time.time()
            print("Zone: %s" % zone)
            try:
                consumption_response = stub.GetConsumption(
                    hvac_consumption_pb2.Request(building=bldg, zone=zone))

                print("Point: "
                      "heating_consumption: %s, cooling_consumption: %s, ventilation_consumption: %s, heating_consumption_stage_two: %s, cooling_consumption_stage_two: %s" %
                      (consumption_response.heating_consumption,
                       consumption_response.cooling_consumption,
                       consumption_response.ventilation_consumption,
                       consumption_response.heating_consumption_stage_two,
                       consumption_response.cooling_consumption_stage_two))



            except grpc.RpcError as e:
                       print(e)
            print("Took: %f seconds" % (time.time() - s_time))
            print("")
        print("")

if __name__ == '__main__':
    run()
