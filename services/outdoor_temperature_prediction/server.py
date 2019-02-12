#python2.7 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. outdoor_temperature.proto

from concurrent import futures
import time
import grpc
import outdoor_temperature_prediction_pb2
import outdoor_temperature_prediction_pb2_grpc
import datetime
import pytz
import requests
import pandas as pd
from dateutil import parser

# getting the utils file here
import os, sys
import xbos_services_utils2 as utils


_ONE_DAY_IN_SECONDS = 60 * 60 * 24
unit = "F" # we will keep the outside temperature in fahrenheit for now.


BUILDING_COORDINATES = {
"orinda-public-library":"37.8830553,-122.1900413",
"orinda-community-center":"37.8830553,-122.1900413",
"hayward-station-1":"37.6465448,-122.1187695",
"hayward-station-8":"37.675162,-122.0322595",
"avenal-animal-shelter":"36.001755,-120.113438",
"avenal-movie-theatre":"36.0026293,-120.137419",
"avenal-public-works-yard":"36.001972,-120.112119",
"avenal-recreation-center":"36.008819,-120.127677",
"avenal-veterans-hall":"36.001972,-120.112119",
"south-berkeley-senior-center":"37.85436,-122.2751013",
"north-berkeley-senior-center":"37.8736888,-122.2750438",
"berkeley-corporation-yard":"37.8660023,-122.2875179",
"word-of-faith-cc":"38.273656,-121.9611537",
"local-butcher-shop":"37.8780587,-122.2715741",
"jesse-turner-center":"34.0961567,-117.5393781",
"ciee":"37.8751,-122.2761",
"csu-dominguez-hills":"33.8633706,-118.2574696"
}


def get_temperature(request):
    """Returns temperatures for a given request or None for client errors."""
    print("received request:", request.building, request.start, request.end, request.window)
    # validate request
    duration = utils.get_window_in_sec(request.window)
    request_length = [len(request.building), request.start, request.end,duration]
    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if duration <= 0:
        return None, "invalid request, duration is negative or zero"
    if request.end > int((time.time()+_ONE_DAY_IN_SECONDS*6)*1e9):
        return None, "invalid request, end date is too far in the future, max is 6 days from now"
    if request.start < int(time.time() * 1e9):
        return None, "invalid request, start date is in the past."
    if request.start >= request.end:
        return None, "invalid request, start date is equal or after end date."
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"
    if request.building not in BUILDING_COORDINATES.keys():
        return None, "invalid request, building not found, supported buildings:"+str(BUILDING_COORDINATES.keys())

    # get weather data
    try:
        coordinates = BUILDING_COORDINATES[request.building]
        weather_meta = requests.get("https://api.weather.gov/points/" + coordinates).json()
        weather_json = requests.get(weather_meta["properties"]["forecastHourly"])
        weather_data_dictionary = weather_json.json()
    except Exception as e:
        print("Failed to fetch data from weather service",e)
        return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=[]), "Failed to fetch data from weather service" + str(e)

    # convert weather data to a pandas Series.
    weather_times = []
    weather_temperatures = []
    for row in weather_data_dictionary["properties"]["periods"]:
        weather_times.append(parser.parse(row["startTime"]))
        if row["temperatureUnit"] =="F":
            weather_temperatures.append(row["temperature"])
        elif row["temperatureUnit"] =="C":
            weather_temperatures.append(9.0/5.0 * row["temperature"] + 32)
        else:
            print("Weather fetch got data which was not Fahrenheit or Celsius. It had units: %s" % row["temperatureUnit"])
            return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=[]), "Weather fetch got data which was not Fahrenheit or Celsius. It had units: %s" % row["temperatureUnit"]
    weather_data = pd.Series(data=weather_temperatures, index=weather_times)

    # return data interpolated to have it start and end at the given times.
    final_data = utils.smart_resample(weather_data,
                                      datetime.datetime.utcfromtimestamp(float(request.start/1e9)).replace(tzinfo=pytz.utc),
                                      datetime.datetime.utcfromtimestamp(float(request.end/1e9)).replace(tzinfo=pytz.utc),
                                      duration/60., method="interpolate")
    # form proper GRPC reply
    temperatures = []
    for index, temp in final_data.iteritems():
        temperatures.append(outdoor_temperature_prediction_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp, unit=unit))
    if len(temperatures) ==0:
        return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=temperatures), "No data was found for given request"
    return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=temperatures), None

class OutdoorTemperatureServicer(outdoor_temperature_prediction_pb2_grpc.OutdoorTemperatureServicer):
    def GetTemperature(self, request, context):
        temperatures,error = get_temperature(request)
        if temperatures is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return outdoor_temperature_prediction_pb2.TemperatureReply()
        elif error is not None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(error)
            return temperatures
        else:
            return temperatures


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    outdoor_temperature_prediction_pb2_grpc.add_OutdoorTemperatureServicer_to_server(OutdoorTemperatureServicer(), server)
    server.add_insecure_port('[::]:50059')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
