__author__ = "Pranav Gupta"
__email__ = "pranavhgupta@lbl.gov"

""" gRPC Server & client examples - https://grpc.io/docs/tutorials/basic/python.html """

import time
import pytz
import grpc
from concurrent import futures
from datetime import datetime
from collections import defaultdict

import pymortar
import xbos_services_getter

import meter_data_historical_pb2
import meter_data_historical_pb2_grpc
import os

METER_DATA_HOST_ADDRESS = os.environ["METER_DATA_HISTORICAL_HOST_ADDRESS"]
_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def get_meter_data(pymortar_client, pymortar_objects, site, start, end,
                   point_type="Green_Button_Meter", agg='MEAN', window='15m'):
    """ Get meter data from pymortar.

    Parameters
    ----------
    pymortar_client     : pymortar.Client({})
        Pymortar Client Object.
    pymortar_objects    : dict
        Dictionary that maps aggregation values to corresponding pymortar objects.
    site                : str
        Building name.
    start               : str
        Start date - 'YYYY-MM-DDTHH:MM:SSZ'
    end                 : str
        End date - 'YYYY-MM-DDTHH:MM:SSZ'
    point_type          : str
        Type of data, i.e. Green_Button_Meter, Building_Electric_Meter...
    agg                 : str
        Values include MEAN, MAX, MIN, COUNT, SUM, RAW (the temporal window parameter is ignored)
    window              : str
        Size of the moving window.

    Returns
    -------
    pd.DataFrame(), defaultdict(list)
        Meter data, dictionary that maps meter data's columns (uuid's) to sitenames.

    """

    agg = pymortar_objects.get(agg, 'ERROR')

    if agg == 'ERROR':
        raise ValueError('Invalid aggregate type; should be string and in caps; values include: ' +
                         pymortar_objects.keys())

    query_meter = "SELECT ?meter WHERE { ?meter rdf:type brick:" + point_type + " };"

    # Define the view of meters (metadata)
    meter = pymortar.View(
        name="view_meter",
        sites=[site],
        definition=query_meter
    )

    # Define the meter timeseries stream
    data_view_meter = pymortar.DataFrame(
        name="data_meter",  # dataframe column name
        aggregation=agg,
        window=window,
        timeseries=[
            pymortar.Timeseries(
                view="view_meter",
                dataVars=["?meter"]
            )
        ]
    )

    # Define timeframe
    time_params = pymortar.TimeParams(
        start=start,
        end=end
    )

    # Form the full request object
    request = pymortar.FetchRequest(
        sites=[site],
        views=[meter],
        dataFrames=[data_view_meter],
        time=time_params
    )

    # Fetch data from request
    response = pymortar_client.fetch(request)

    # resp_meter = (url, uuid, sitename)
    resp_meter = response.query('select * from view_meter')

    # Map's uuid's to the site names
    map_uuid_sitename = defaultdict(list)
    for (url, uuid, sitename) in resp_meter:
        map_uuid_sitename[uuid].append(sitename)

    return response['data_meter'], map_uuid_sitename


def get_historical_data(request, pymortar_client, pymortar_objects):
    """ Get historical meter data using pymortar and create gRPC repsonse object.

    Parameters
    ----------
    request                 : gRPC request
        Contains parameters to fetch data.
    pymortar_client     : pymortar.Client({})
        Pymortar Client Object.
    pymortar_objects    : dict
        Dictionary that maps aggregation values to corresponding pymortar objects.

    Returns
    -------
    gRPC response, str
        List of points containing the datetime and power consumption; Error Message

    """

    start_time = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_time = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    try:
        df, map_uuid_meter = get_meter_data(pymortar_client=pymortar_client,
                                            pymortar_objects=pymortar_objects,
                                            site=request.building,
                                            point_type=request.point_type,
                                            start=start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                            end=end_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                                            agg=request.aggregate,
                                            window=request.window)
    except Exception as e:
        return None, e

    if len(df.columns) == 2:
        df[df.columns[0]] = df[df.columns[0]] + df[df.columns[1]]
        df = df.drop(columns=[df.columns[1]])

    df.columns = ['power']

    result = []
    for index, row in df.iterrows():
        point = meter_data_historical_pb2.MeterDataPoint(time=int(index.timestamp()*1e9), power=row['power'])
        result.append(point)

    return meter_data_historical_pb2.Reply(point=result), None


def get_parameters(request, supported_buildings):
    """ Storing and error checking request parameters.

    Parameters
    ----------
    request                 : gRPC request
        Contains parameters to fetch data.
    supported_buildings     : list(str)
        List of buildings available.

    Returns
    -------
    str
        Error message. If no error message, then return None.

    """

    start_time = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_time = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    if any(not elem for elem in [request.building, start_time, end_time,
                                 request.aggregate, request.window, request.point_type]):
        return "invalid request, empty param(s)"

    if request.start > int(time.time() * 1e9) or request.end > int(time.time() * 1e9):
        return "invalid request, start/end date is in the future"

    if request.start >= request.end:
        return "invalid request, start date is equal or after end date."

    if request.building not in supported_buildings:
        return "invalid request, building not found; supported buildings: " + str(self.supported_buildings)

    return None

    # # Other error checkings
    # duration = utils.get_window_in_sec(request.window)
    # if duration <= 0:
    #     return None, "invalid request, duration is negative or zero"
    # if request.start + (duration * 1e9) > request.end:
    #     return None, "invalid request, start date + window is greater than end date"


class MeterDataHistoricalServicer(meter_data_historical_pb2_grpc.MeterDataHistoricalServicer):

    def __init__(self):
        """ Constructor.

        Note
        ----
        For pymortar, set the evironment variables - $MORTAR_API_USERNAME & $MORTAR_API_PASSWORD.

        For Mac,
        1. vi ~/.bash_profile
        2. Add at the end of file,
            1. export $MORTAR_API_USERNAME=username
            2. export $MORTAR_API_PASSWORD=password
        3. source ~/.bash_profile

        """

        # Pymortar client
        self.pymortar_client = pymortar.Client()

        # List of zones in building
        building_names_stub = xbos_services_getter.get_building_zone_names_stub()
        self.supported_buildings = xbos_services_getter.get_buildings(building_names_stub)

        self.pymortar_objects = {
            'MEAN': pymortar.MEAN,
            'MAX': pymortar.MAX,
            'MIN': pymortar.MIN,
            'COUNT': pymortar.COUNT,
            'SUM': pymortar.SUM,
            'RAW': pymortar.RAW
        }

    def GetMeterDataHistorical(self, request, context):
        """ RPC.

        Parameters
        ----------
        request     : gRPC request
            Contains parameters to fetch data.
        context     : ???
            ???

        Returns
        -------
        gRPC response
            List of points containing the datetime and power consumption.

        """

        error = get_parameters(request, self.supported_buildings)
        if error:
            # List of status codes: https://github.com/grpc/grpc/blob/master/doc/statuscodes.md
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return meter_data_historical_pb2.Reply()
        else:
            result, error = get_historical_data(request, self.pymortar_client, self.pymortar_objects)
            if error:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
                return meter_data_historical_pb2.Reply()
        return result


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    meter_data_historical_pb2_grpc.add_MeterDataHistoricalServicer_to_server(MeterDataHistoricalServicer(), server)
    server.add_insecure_port(METER_DATA_HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
