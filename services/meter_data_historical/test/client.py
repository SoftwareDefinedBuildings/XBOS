import grpc
import pandas as pd
from pathlib import Path
import sys
sys.path.append(str(Path.cwd().parent))
import os

import MeterData_pb2
import MeterData_pb2_grpc

METER_DATA_HOST_ADDRESS = os.environ["METER_DATA_HISTORICAL_HOST_ADDRESS"]


def run():

    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel(METER_DATA_HOST_ADDRESS) as channel:

        stub = MeterData_pb2_grpc.MeterDataStub(channel)

        try:

            # start and end time should have the same format, i.e. 'YYYY-MM-DDTHH:MM:SSZ'
            start = '2018-01-01T00:00:00Z'
            end = '2018-01-15T00:00:00Z'
            point_type = 'Building_Electric_Meter'
            aggregate = 'MEAN'
            window = '15m'

            # Note: bldg expects a type - list(str), so even for 1 site, encapsulate it in a list
            bldg = ["ciee"]

            # Create gRPC request object
            request = MeterData_pb2.Request(
                buildings=bldg,
                start=start,
                end=end,
                point_type=point_type,
                aggregate=aggregate,
                window=window
            )

            response = stub.GetMeterData(request)

            df = pd.DataFrame()
            for point in response.point:
                df = df.append([[point.time, point.power]])

            df.columns = ['datetime', 'power']
            df.set_index('datetime', inplace=True)
            df.to_csv(bldg[0] + '.csv')

        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':

    run()
