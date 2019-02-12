
from __future__ import print_function

import grpc
import time
import datetime
import hvac_consumption_pb2
import hvac_consumption_pb2_grpc

import calendar
import pytz

import sys
sys.path.append("..")
import utils

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.

    all_bldgs = utils.get_buildings()

    channel = grpc.insecure_channel('localhost:50056')
    stub = hvac_consumption_pb2_grpc.ConsumptionHVACStub(channel)

    for bldg in all_bldgs:
        # case 1, Test from now into future
        print("Building: %s" % bldg)
        for zone in utils.get_zones(bldg):
            s_time = time.time()
            print("Zone: %s" % zone)
            try:
                d_start = (datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=20))

                # d_start = datetime.datetime(year=2018, month=9, day=8, hour=21, minute=31, second=10).replace(tzinfo=pytz.utc)
                start = calendar.timegm(d_start.utctimetuple()) * 1e9

                end = calendar.timegm((datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(
                    days=15)).utctimetuple()) * 1e9

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
