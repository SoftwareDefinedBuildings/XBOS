
from __future__ import print_function

import grpc
import time
import datetime

from pathlib import Path
import sys
sys.path.append(str(Path.cwd().parent))
import temperature_bands_pb2
import temperature_bands_pb2_grpc

import pytz

import xbos_services_utils3 as utils

import os
TEMPERATURE_BANDS_HOST_ADDRESS = os.environ["TEMPERATURE_BANDS_HOST_ADDRESS"]


def run():

    all_bldgs = utils.get_buildings()

    channel = grpc.insecure_channel(TEMPERATURE_BANDS_HOST_ADDRESS)
    stub = temperature_bands_pb2_grpc.SchedulesStub(channel)

    for bldg in all_bldgs:
        # case 1, Test from now into future
        print("Building: %s" % bldg)
        for zone in utils.get_zones(bldg):
            s_time = time.time()
            print("Zone: %s" % zone)

            try:

                end = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) + datetime.timedelta(days=1)
                end_unix = int(end.timestamp() * 1e9)
                start = end - datetime.timedelta(days=7)
                start_unix = int(start.timestamp() * 1e9)

                window = "5m"
                units = "F"

                comfortband_response = stub.GetComfortband(
                    temperature_bands_pb2.Request(building=bldg, zone=zone, start=start_unix, end=end_unix, unit=units,
                                                  window=window))

                do_not_exceed_response = stub.GetDoNotExceed(temperature_bands_pb2.Request(building=bldg, zone=zone, start=start_unix, end=end_unix, unit=units,
                                                  window=window))

                for point in comfortband_response.schedules:
                    ts = int(point.time / 1e9)
                    print("Comfort point at: %s is t_low: %f and t_high: %f" % (
                    datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ' PST',
                    point.temperature_low,
                    point.temperature_high))

                for point in do_not_exceed_response.schedules:
                    ts = int(point.time / 1e9)
                    print("Do not exceed point at: %s is t_low: %f and t_high: %f" % (
                    datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + ' PST',
                    point.temperature_low,
                    point.temperature_high))

            except grpc.RpcError as e:
                print(e)
            print("Took: %f seconds" % (time.time() - s_time))
            print("")
        print("")

if __name__ == "__main__":
    run()