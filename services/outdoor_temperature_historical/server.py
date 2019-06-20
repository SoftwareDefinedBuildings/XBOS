from concurrent import futures
import time
import grpc
import logging
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.DEBUG)
import pymortar
import outdoor_temperature_historical_pb2
import outdoor_temperature_historical_pb2_grpc
import csv
import os, sys
from datetime import datetime
from rfc3339 import rfc3339
from numpy import nan
import pytz
import pandas as pd
from fbprophet import Prophet
from pathlib import Path
import logging
import traceback

logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS = os.environ["OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS"]
OUTDOOR_TEMPERATURE_HISTORICAL_DATA_PATH = Path(os.environ["OUTDOOR_TEMPERATURE_HISTORICAL_DATA_PATH"])


_ONE_DAY_IN_SECONDS = 60 * 60 * 24

pymortar_objects = {
    'MEAN': pymortar.MEAN,
    'MAX': pymortar.MAX,
    'MIN': pymortar.MIN,
    'COUNT': pymortar.COUNT,
    'SUM': pymortar.SUM,
    'RAW': pymortar.RAW
}


def train_models(weather_mapping,pymortar_client):
    logging.info("about to train all models")
    fb_prophet_models ={}
    start = pytz.timezone('US/Pacific').localize(datetime(year=2013, month=1, day=1, hour=0, minute=0))
    end = pytz.timezone('US/Pacific').localize(datetime.now())
    window = get_window_in_sec("15m") # will be ignored since we are requesting raw data
    agg = pymortar.RAW
    for bldg in weather_mapping.Building:
        uuid = weather_mapping.loc[weather_mapping.Building==bldg].UUID.item()
        logging.info("training model for building: %s with uuid: %s",bldg,uuid)
        raw,err = get_mortar_oat_uuid(uuid,start,end,window,agg,pymortar_client)
        if raw is None:
            logging.critical("Error: failed to fetch raw data for building: %s with uuid: %s",bldg,uuid)
            sys.exit()
        df = pd.DataFrame({'ds':raw.index, 'y':raw[uuid]})
        df.reset_index(inplace=True)
        df.ds = df.ds.dt.tz_localize(None)
        df.pop('index')
        m = Prophet()
        fb_prophet_models[bldg]=m.fit(df)
    logging.info("finished training all models, ready to serve")
    return fb_prophet_models


def _get_prophet_temperature(m, start, end, window):
    df = pd.DataFrame({'ds': pd.date_range(start, end, freq=str(int(window)) + 'S').tz_localize(None)})
    forecast = m.predict(df)
    output = forecast[['ds', 'yhat']]
    return output.set_index(pd.to_datetime(output.pop('ds'))), None


def get_mortar_oat_uuid( uuid, start, end, window, agg, pymortar_client):
    oat_df = pymortar.DataFrame(
        name="weather_stations",
        uuids=[uuid],
        aggregation=agg,
        window=str(int(window)) + 's',
    )

    oat_time_params = pymortar.TimeParams(
        start=rfc3339(start),
        end=rfc3339(end),
    )

    oat_request = pymortar.FetchRequest(
        sites=[""],
        dataFrames=[
            oat_df
        ],
        time=oat_time_params
    )
    outside_temperature_data = pymortar_client.fetch(oat_request)['weather_stations']
    if outside_temperature_data is None:
        return None, "did not fetch data from pymortar for uuid: %s" % uuid

    return outside_temperature_data, None


def get_mortar_oat_building(building,start,end,window, agg, pymortar_client):
    outside_temperature_query = """SELECT ?temp WHERE {
        ?temp rdf:type brick:Weather_Temperature_Sensor
    };"""

    weather_stations_view = pymortar.View(
        name='weather_stations_view',
        sites=[building],
        definition=outside_temperature_query
    )
    weather_stations_stream = pymortar.DataFrame(
        name='weather_stations',
        aggregation=agg,
        window=str(int(window)) + 's',
        timeseries=[
            pymortar.Timeseries(
                view='weather_stations_view',
                dataVars=['?temp']
            )
        ]
    )
    weather_stations_time_params = pymortar.TimeParams(
        start=rfc3339(start),
        end=rfc3339(end),
    )

    request = pymortar.FetchRequest(
        sites=[building],
        views=[weather_stations_view],
        dataFrames=[weather_stations_stream],
        time=weather_stations_time_params
    )
    outside_temperature_data = pymortar_client.fetch(request)['weather_stations']
    if outside_temperature_data is None:
        return None, "did not fetch data from pymortar with query: %s" % outside_temperature_query

    return outside_temperature_data, None


def _get_raw_temperature(uuid, start, end, window,agg, pymortar_client):

    raw_outside_data, err = get_mortar_oat_uuid(uuid,start,end,window,agg,pymortar_client)
    if raw_outside_data is None:
        return None, err

    # Due to a bug, nan values were stored as 32. TODO remove this line if the bug is fixed
    raw_outside_data = raw_outside_data.applymap(lambda t: nan if t == 32 else t)

    return raw_outside_data, None


def get_preprocessed_temperature(request, fb_prophet_models, weather_mapping):
    """Returns temperatures for a given request or None.
    Guarantees that no Nan values in returned data exist."""
    logging.info("received request: %s %s %s %s", request.building, request.start, request.end, request.window)
    duration = get_window_in_sec(request.window)

    unit = "F" # we will keep the outside temperature in fahrenheit for now.

    request_length = [len(request.building), request.start, request.end,
                      duration]
    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if request.start >= request.end:
        return None, "invalid request, start date is after end date."
    if request.start < 0 or request.end < 0:
        return None, "invalid request, negative dates"
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"
    if request.building not in weather_mapping["Building"].values:
        return None, "invalid request, invalid building name, supported buildings are: "++str(list(weather_mapping["Building"].values))

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    final_data, err = _get_prophet_temperature(fb_prophet_models[request.building], d_start, d_end, duration)
    if final_data is None:
        return [outdoor_temperature_historical_pb2.TemperaturePoint()], err

    temperatures = []

    for index, temp in final_data.iterrows():
        temperatures.append(outdoor_temperature_historical_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp.item(), unit=unit))
    return temperatures, None


def get_raw_temperature(request, pymortar_client, weather_mapping):
    """Returns temperatures for a given request or None.
    Guarantees that no Nan values in returned data exist."""
    logging.info("received request: %s %s %s %s %s", request.building, request.start, request.end, request.window, request.aggregate)
    duration = get_window_in_sec(request.window)

    unit = "F" # we will keep the outside temperature in fahrenheit for now.

    request_length = [len(request.building), request.start, request.end,
                      duration,len(request.aggregate)]
    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if request.end > int(time.time() * 1e9):
        return None, "invalid request, end date is in the future."
    if request.start >= request.end:
        return None, "invalid request, start date is after end date."
    if request.start < 0 or request.end < 0:
        return None, "invalid request, negative dates"
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"
    if request.building not in weather_mapping["Building"].values:
        return None, "invalid request, invalid building name, supported buildings are: "++str(list(weather_mapping["Building"].values))

    agg = pymortar_objects.get(request.aggregate.upper(), 'ERROR')
    if agg == 'ERROR':
        return None, "invalid request, invalid aggregate type should be string from one of: %s " % pymortar_objects.keys()

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    final_data, err = _get_raw_temperature(weather_mapping.loc[weather_mapping.Building==request.building].UUID.item(), d_start, d_end, duration, agg, pymortar_client)
    if final_data is None:
        return [outdoor_temperature_historical_pb2.TemperaturePoint()], err

    temperatures = []

    for index, temp in final_data.iterrows():
        temperatures.append(outdoor_temperature_historical_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp.item(), unit=unit))
    return temperatures, None


def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
       Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0


class OutdoorTemperatureServicer(outdoor_temperature_historical_pb2_grpc.OutdoorTemperatureServicer):
    def __init__(self):
        try:
            self.pymortar_client = pymortar.Client()
            outdoor_temperature_historical_path = OUTDOOR_TEMPERATURE_HISTORICAL_DATA_PATH / "weather-mapping.csv"
            if not os.path.isfile(str(outdoor_temperature_historical_path)):
                logging.critical("Error: could not find file at: %s" , str(outdoor_temperature_historical_path))
                sys.exit()
            self.weather_mapping = pd.read_csv(str(outdoor_temperature_historical_path))
            self.fb_prophet_models = train_models(self.weather_mapping,self.pymortar_client)
            print("ready to serve")
        except Exception:
            tb = traceback.format_exc()
            logging.critical("Error: failed to initialize microservice or models: %s" , tb)
            sys.exit()


    def GetPreprocessedTemperature(self, request, context):
        try:
            temperatures,error = get_preprocessed_temperature(request, self.fb_prophet_models, self.weather_mapping)
            if temperatures is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return outdoor_temperature_historical_pb2.TemperaturePoint()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            for temp in temperatures:
                yield temp
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return outdoor_temperature_historical_pb2.TemperaturePoint()


    def GetRawTemperature(self, request, context):
        try:
            temperatures,error = get_raw_temperature(request, self.pymortar_client, self.weather_mapping)
            if temperatures is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return outdoor_temperature_historical_pb2.TemperaturePoint()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            for temp in temperatures:
                yield temp
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return outdoor_temperature_historical_pb2.TemperaturePoint()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    outdoor_temperature_historical_pb2_grpc.add_OutdoorTemperatureServicer_to_server(OutdoorTemperatureServicer(), server)
    server.add_insecure_port(OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS)
    logging.info("Serving on {0}".format(OUTDOOR_TEMPERATURE_HISTORICAL_HOST_ADDRESS))
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
