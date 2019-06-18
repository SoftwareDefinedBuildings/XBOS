from concurrent import futures
import time
import grpc
import logging
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.DEBUG)
import outdoor_temperature_prediction_pb2
import outdoor_temperature_prediction_pb2_grpc
import datetime
import pytz
import requests
import pandas as pd
import numpy as np
from dateutil import parser


import os
OUTDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS = os.environ["OUTDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS"]
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
"berkeley-corporate-yard":"37.8660023,-122.2875179",
"word-of-faith-cc":"38.273656,-121.9611537",
"local-butcher-shop":"37.8780587,-122.2715741",
"jesse-turner-center":"34.0961567,-117.5393781",
"ciee":"37.8751,-122.2761",
"csu-dominguez-hills":"33.8633706,-118.2574696"
}

def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
       Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0

def smart_resample(data, start, end, window, method):
    """
    Groups data into intervals according to the method used.
    Returns data indexed with start to end in frequency of interval minutes.
    :param data: pd.series/pd.df has to have time series index which can contain a span from start to end. Timezone aware.
    :param start: the start of the data we want. Timezone aware
    :param end: the end of the data we want (not inclusive). Timezone aware
    :param window: (int seconds) interval length in which to split data.
    :param method: (optional string) How to fill nan values. Usually use pad (forward fill for setpoints) and
                            use "interpolate" for approximate linear processes (like outside temperature. For inside
                            temperature we would need an accurate thermal model.)
    :return: data with index of pd.date_range(start, end, interval). Returned in timezone of start.
    NOTE: - If (end - start) not a multiple of interval, then we choose end = start + (end - start)//inteval * interval.
                But the new end will not be inclusive.
          - If end is beyond the end of the data, it will assume that the last value has been constant until the
              given end.
    """
    try:
         end = end.astimezone(start.tzinfo)
         data = data.tz_convert(start.tzinfo)
    except:
         raise Exception("Start, End, Data need to be timezone aware.")


    # make sure that the start and end dates are valid.
    data = data.sort_index()
    if not start <= end:
        raise Exception("Start is after End date.")
    if not start >= data.index[0]:
        raise Exception("Resample start date is further back than data start date -- can not resample.")
    if not window > 0:
        raise Exception("Interval has to be larger than 0.")

    # add date_range and fill nan's through the given method.
    date_range = pd.date_range(start, end, freq=str(window) + "S")
    end = date_range[-1]  # gets the right end.

    # Raise warning if we don't have enough data.
    if end - datetime.timedelta(seconds=window) > data.index[-1]:
        logging.warning("Warning: the given end is more than one interval after the last datapoint in the given data. %s minutes after end of data."
              % str((end - data.index[-1]).total_seconds()/60.))

    new_index = date_range.union(data.index).tz_convert(date_range.tzinfo)
    data_with_index = data.reindex(new_index)

    if method == "interpolate":
        data = data_with_index.interpolate("time")
    elif method in ["pad", "ffill"]:
        data = data_with_index.fillna(method=method)
    else:
        raise Exception("Incorrect method for filling nan values given.")

    data = data.loc[start: end]  # While we return data not inclusive, we need last datapoint for weighted average.

    def weighted_average_constant(datapoint, window):
        """Takes time weighted average of data frame. Each datapoint is weighted from its start time to the next
        datapoints start time.
        :param datapoint: pd.df/pd.series. index includes the start of the interval and all data is between start and start + interval.
        :param window: int seconds.
        :returns the value in the dataframe weighted by the time duration."""
        datapoint = datapoint.sort_index()
        temp_index = np.array(list(datapoint.index) + [datapoint.index[0] + datetime.timedelta(seconds=window)])
        diffs = temp_index[1:] - temp_index[:-1]
        weights = np.array([d.total_seconds() for d in diffs]) / float(window)
        assert 0.99 < sum(weights) < 1.01  # account for tiny precision errors.
        if isinstance(datapoint, pd.DataFrame):
            return pd.DataFrame(index=[datapoint.index[0]], columns=datapoint.columns, data=[datapoint.values.T.dot(weights)])
        else:
            return pd.Series(index=[datapoint.index[0]], data=datapoint.values.dot(weights))

    def weighted_average_linear(datapoint, window, full_data):
        """Takes time weighted average of data frame. Each datapoint is weighted from its start time to the next
        datapoints start time.
        :param datapoint: pd.df/pd.series. index includes the start of the interval and all data is between start and start + interval.
        :param window: int seconds.
        :returns the value in the dataframe weighted by the time duration."""
        datapoint = datapoint.sort_index()
        temp_index = np.array(list(datapoint.index) + [datapoint.index[0] + datetime.timedelta(seconds=window)])

        if isinstance(datapoint, pd.DataFrame):
            temp_values = np.array(
                list(datapoint.values) + [full_data.loc[temp_index[-1]].values])
        else:
            temp_values = np.array(list(datapoint.values) + [full_data.loc[temp_index[-1]]])

        new_values = []
        for i in range(0, len(temp_values)-1):
            new_values.append((temp_values[i+1] + temp_values[i])/2.)

        new_values = np.array(new_values)
        diffs = temp_index[1:] - temp_index[:-1]
        weights = np.array([d.total_seconds() for d in diffs]) / float(window)

        assert 0.99 < sum(weights) < 1.01  # account for tiny precision errors.
        if isinstance(datapoint, pd.DataFrame):
            return pd.DataFrame(index=[datapoint.index[0]], columns=datapoint.columns, data=[new_values.T.dot(weights)])
        else:
            return pd.Series(index=[datapoint.index[0]], data=new_values.dot(weights))

    if method == "interpolate":
        # take weighted average and groupby datapoints which are in the same interval.
        data_grouped = data.iloc[:-1].groupby(by=lambda x: (x - start).total_seconds() // window, group_keys=False).apply(func=lambda x: weighted_average_linear(x, window, data))
    else:
        data_grouped = data.iloc[:-1].groupby(by=lambda x: (x - start).total_seconds() // window, group_keys=False).apply(func=lambda x: weighted_average_constant(x, window))

    return data_grouped


def get_temperature(request):
    """Returns temperatures for a given request or None for client errors."""
    logging.info("received request:", request.building, request.start, request.end, request.window)
    # validate request
    duration = get_window_in_sec(request.window)
    request_length = [len(request.building), request.start, request.end,duration]
    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if duration <= 0:
        return None, "invalid request, window is negative or zero"
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
        if "properties" not in weather_data_dictionary or "periods" not in weather_data_dictionary["properties"]:
            logging.error("Failed to fetch data from weather service",e)
            return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=[]), "Failed to fetch data from weather service" + str(e)
    except Exception as e:
        logging.error("Failed to fetch data from weather service",e)
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
            logging.warning("Weather fetch got data which was not Fahrenheit or Celsius. It had units: %s" % row["temperatureUnit"])
            return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=[]), "Weather fetch got data which was not Fahrenheit or Celsius. It had units: %s" % row["temperatureUnit"]
    weather_data = pd.Series(data=weather_temperatures, index=weather_times)

    # return data interpolated to have it start and end at the given times.
    final_data = smart_resample(weather_data,
                                      datetime.datetime.utcfromtimestamp(int(request.start/1e9)).replace(tzinfo=pytz.utc),
                                      datetime.datetime.utcfromtimestamp(int(request.end/1e9)).replace(tzinfo=pytz.utc),
                                      duration, method="interpolate")
    # form proper GRPC reply
    temperatures = []
    for index, temp in final_data.iteritems():
        temperatures.append(outdoor_temperature_prediction_pb2.TemperaturePoint(time=int(index.timestamp() * 1e9), temperature=temp, unit=unit))
    if len(temperatures) ==0:
        return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=temperatures), "No data was found for given request"
    return outdoor_temperature_prediction_pb2.TemperatureReply(temperatures=temperatures), None

class OutdoorTemperatureServicer(outdoor_temperature_prediction_pb2_grpc.OutdoorTemperatureServicer):
    def __init__(self):
        pass

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
    server.add_insecure_port(OUTDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS)
    logging.info("Serving on {0}".format(OUTDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS))
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
