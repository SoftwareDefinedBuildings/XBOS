__author__ = "Pranav Gupta"
__email__ = "pranavhgupta@lbl.gov"

import os
import grpc
import pandas as pd
from pathlib import Path

import sys
sys.path.append(str(Path.cwd().parent))

import MeterDataHistorical_pb2
import MeterDataHistorical_pb2_grpc

# CHECK: Change port!
METER_DATA_HOST_ADDRESS = 'localhost:1234'


def run():

    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel(METER_DATA_HOST_ADDRESS) as channel:

        stub = MeterDataHistorical_pb2_grpc.MeterDataHistoricalStub(channel)

        try:

            start = 1514764800000000000  # Monday, January 1, 2018 12:00:00 AM UTC
            end = 1514786400000000000  # Wednesday, January 1, 2018 06:00:00 AM UTC
            point_type = 'Building_Electric_Meter'
            aggregate = 'RAW'
            window = '15m' # Will be ignored, since aggregate=RAW
            bldg = "ciee"

            # Create gRPC request object
            request = MeterDataHistorical_pb2.Request(
                building=bldg,
                start=start,
                end=end,
                point_type=point_type,
                aggregate=aggregate,
                window=window
            )

            response = stub.GetMeterDataHistorical(request)

            # NOTE
            # Converting list(dic) to pd.DataFrame is significantly faster than appending a single row to pd.DataFrame.
            row_list = []
            for point in response.point:
                dic = {
                    'datetime': point.time,
                    'power': point.power
                }
                row_list.append(dic)

            df = pd.DataFrame(row_list)
            df.set_index('datetime', inplace=True)

            # Store the dataframe in "data/" folder
            data_folder = 'data'
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
            df.to_csv(data_folder + '/' + bldg + '.csv')

        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
    run()
