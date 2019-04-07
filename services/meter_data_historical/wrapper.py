"""
# Building and Zone names
def get_building_zone_names_stub(BUILDING_ZONE_NAMES_HOST_ADDRESS=None):
    ""Get the stub to interact with the building_zone_address service.
    :param BUILDING_ZONE_NAMES_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.
    ""

    if BUILDING_ZONE_NAMES_HOST_ADDRESS is None:
        BUILDING_ZONE_NAMES_HOST_ADDRESS = os.environ["BUILDING_ZONE_NAMES_HOST_ADDRESS"]

    channel = grpc.insecure_channel(BUILDING_ZONE_NAMES_HOST_ADDRESS)
    stub = building_zone_names_pb2_grpc.BuildingZoneNamesStub(channel)
    return stub


def get_buildings(building_zone_names_stub):
    ""Gets all the building names supported by the services.
    :param building_zone_names_stub: grpc stub for building_zone_names service.
    :return: list (string) building names.
    ""

    building_names = building_zone_names_stub.GetBuildings(building_zone_names_pb2.BuildingRequest())
    return [bldg.name for bldg in building_names.names]
"""

import os
import grpc

import MeterData_pb2
import MeterData_pb2_grpc

def get_meter_data_stub(METER_DATA_HOST_ADDRESS=None):
    """ Get stub to interact with meter data service.
    :param METER_DATA_HOST_ADDRESS: Optional argument to supply host address for given service. Otherwise,
        set as environment variable.
    :return: grpc Stub object.
    """

    if not METER_DATA_HOST_ADDRESS:
        METER_DATA_HOST_ADDRESS = os.environ["METER_DATA_HOST_ADDRESS"]

    channel = grpc.insecure_channel(METER_DATA_HOST_ADDRESS)
    stub = MeterData_pb2_grpc.MeterDataStub(channel)
    return stub

def get_meter_data(meter_data_stub, bldg, start, end, point_type, aggregate, window):
    """ Get meter data as a dataframe.

    :param meter_data_stub: grpc stub for meter data service.
    :param bldg: list(str) - list of buildings.
    :param start: (str) start time. format - 'YYYY-MM-DDTHH:MM:SSZ' Z denotes UTC.
    :param end: (str) end time. format - 'YYYY-MM-DDTHH:MM:SSZ' Z denotes UTC.
    :param point_type: (str) Building_Electric_Meter or Green_Button_Meter
    :param aggregate: (str) Values include MEAN, MAX, MIN, COUNT, SUM and RAW (the temporal window parameter is ignored)
    :param window: (str) Size of the moving window.
    :return: pd.DataFrame(), defaultdict(list) - Meter data, dictionary that maps meter data's columns (uuid's) to sites
    """

    # Create gRPC request object
    request = MeterData_pb2.Request(
        buildings=bldg,
        start=start,
        end=end,
        point_type=point_type,
        aggregate=aggregate,
        window=window
    )

    response = meter_data_stub.GetMeterData(request)

    df = pd.DataFrame()
    for point in response.point:
        df = df.append([[point.time, point.power]])

    df.columns = ['datetime', 'power']
    df.set_index('datetime', inplace=True)

    return df

