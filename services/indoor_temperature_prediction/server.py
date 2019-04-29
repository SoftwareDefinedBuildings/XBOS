import os, sys

import datetime
import pytz
import pandas as pd
import numpy as np

from concurrent import futures
import time
import grpc

import indoor_temperature_prediction_pb2
import indoor_temperature_prediction_pb2_grpc

import create_models as ctm

import xbos_services_getter as xsg

HOST_ADDRESS = os.environ["INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS"]

_INTERVAL = "5m"  # minutes # TODO allow for getting multiples of 5. Prediction horizon.
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

THERMAL_MODELS = {}

END = datetime.datetime(year=2019, month=4, day=1).replace(
    tzinfo=pytz.utc)  # datetime.datetime.utcnow().replace(tzinfo=pytz.utc) # TODO make environ var.
START = END - datetime.timedelta(days=120)  # TODO Put back to 120


def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
    Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0


def initizalize():
    building_zone_names_stub = xsg.get_building_zone_names_stub()
    all_building_zone_names = xsg.get_all_buildings_zones(building_zone_names_stub)
    for building in all_building_zone_names.keys():
        print("Initizalizing building:", building)
        for zone in all_building_zone_names[building]:
            print("Zone:", zone)
            _, err = check_thermal_model(building, zone)
            if err is not None:
                print("Error: " + err)
        print("")


def check_thermal_model(building, zone):
    if building not in THERMAL_MODELS or zone not in THERMAL_MODELS[building]:
        # TODO ERROR CHECK.
        thermal_model, column_order, err = training(building, zone, START, END)
        if err is not None:
            return None, err
        if building not in THERMAL_MODELS:
            THERMAL_MODELS[building] = {}
        THERMAL_MODELS[building][zone] = (thermal_model, column_order)

    return None, None


def training(building, zone, start, end):
    """

    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :return: Trained thermal model object.
    """
    # TODO add more error checking here goddamn
    model, column_order, err = ctm.create_model(building=building,
                                                zone=zone,
                                                start=start,
                                                end=end,
                                                prediction_window=_INTERVAL,
                                                raw_data_granularity="1m",
                                                train_ratio=1,
                                                is_second_order=True,
                                                use_occupancy=False,
                                                curr_action_timesteps=0,
                                                prev_action_timesteps=-1,
                                                method="OLS",
                                                check_data=False)  # change this as needed.
    if err is not None:
        return None, None, err
    return model, column_order, None


def get_error(request):
    """Gets error for prediction + error = label.

    :return: error_reply, err
    """
    print("received request:", request.building, request.zone, request.action, request.start, request.end, request.unit)

    request_length = [len(request.building), len(request.zone), request.start,
                      request.end,
                      len(request.unit)]

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if not (0 <= request.action <= 2):
        return None, "invalid request, action is not between 0 and 2."
    if request.unit != "F":
        return None, "invalid request, only support 'F' unit."

    # TODO Check if valid building/zone/temperature unit/zone, outside and indoor temperature (not none)

    start = datetime.datetime.utcfromtimestamp(float(request.start / 1e9)).replace(
        tzinfo=pytz.utc)
    end = datetime.datetime.utcfromtimestamp(float(request.end / 1e9)).replace(
        tzinfo=pytz.utc)

    # checking if we have a thermal model, and training if necessary.
    _, err = check_thermal_model(request.building, request.zone)
    if err is not None:
        return None, "No valid Thermal Model. (" + err + ")"

    train_X, train_y, _, _, err = ctm.get_train_test(building=request.building,
                                                     zone=request.zone,
                                                     start=start,
                                                     end=end,
                                                     prediction_window=_INTERVAL,
                                                     raw_data_granularity="1m",
                                                     train_ratio=1,
                                                     is_second_order=True,
                                                     use_occupancy=False,
                                                     curr_action_timesteps=0,
                                                     prev_action_timesteps=-1,
                                                     check_data=False)

    if err is not None:
        return None, None, err

    thermal_model, column_order = THERMAL_MODELS[request.building][request.zone]
    if request.action != -1:
        filter = train_X["action"] == request.action
        train_X = train_X[filter]
        train_y = train_y[filter]
    predictions_train = thermal_model.predict(train_X)
    error = (train_y.values - predictions_train)

    err_mean, err_var = np.mean(error), np.var(error)

    error_reply = indoor_temperature_prediction_pb2.ErrorReply(
        mean=err_mean,
        var=err_var,
        unit="F")
    return error_reply, None


def prediction(request):
    """Returns temperature prediction for a given request or None."""

    print("received request:", request.building, request.zone, request.current_time,
          request.indoor_temperature, request.outside_temperature, request.other_zone_temperatures,
          request.temperature_unit)

    request_length = [len(request.building), len(request.zone), request.current_time,
                      request.indoor_temperature, request.outside_temperature, request.other_zone_temperatures,
                      len(request.temperature_unit)]

    unit = "F"  # fahrenheit for now .

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if not (0 <= request.action <= 2):
        return None, "Action is not between 0 and 2."

    # TODO Check if valid building/zone/temperature unit/zone, outside and indoor temperature (not none)

    current_time = datetime.datetime.utcfromtimestamp(float(request.current_time / 1e9)).replace(
        tzinfo=pytz.utc)

    # checking if we have a thermal model, and training if necessary.
    _, err = check_thermal_model(request.building, request.zone)
    if err is not None:
        return None, "No valid Thermal Model. (" + err + ")"
    thermal_model, column_order = THERMAL_MODELS[request.building][request.zone]
    data_point = {
        "t_in": request.indoor_temperature,
        "action": request.action,
        "t_out": request.outside_temperature,
        "dt": get_window_in_sec(_INTERVAL),
        "t_prev": request.previous_indoor_temperature  # TODO t_last feature should be added to proto specs
    }

    for iter_zone, iter_temp in request.other_zone_temperatures.items():
        if iter_zone != request.zone:
            data_point["temperature_zone_" + iter_zone] = iter_temp

    data_point = pd.DataFrame(data=[data_point], index=[current_time])[column_order]

    prediction = thermal_model.predict(data_point)

    prediction_reply = indoor_temperature_prediction_pb2.PredictedTemperatureReply(
        time=int(request.current_time + get_window_in_sec(_INTERVAL) * 1e9),
        temperature=prediction[0],
        unit=unit)
    return prediction_reply, None


class IndoorTemperaturePredictionServicer(indoor_temperature_prediction_pb2_grpc.IndoorTemperaturePredictionServicer):
    def __init__(self):
        pass

    def GetSecondOrderPrediction(self, request, context):
        """A simple RPC.
        """
        predicted_temperature, error = prediction(request)
        if predicted_temperature is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return indoor_temperature_prediction_pb2.PredictedTemperatureReply()
        else:
            return predicted_temperature

    def GetSecondOrderError(self, request, context):
        """A simple RPC.

        """
        error_reply, error = get_error(request)
        if error_reply is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return indoor_temperature_prediction_pb2.PredictedTemperatureReply()
        else:
            return error_reply


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    indoor_temperature_prediction_pb2_grpc.add_IndoorTemperaturePredictionServicer_to_server(
        IndoorTemperaturePredictionServicer(), server)
    server.add_insecure_port(HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    # initizalize()
    serve()
    #
    # building = 'ciee'
    # zone = "HVAC_Zone_Northzone"
    #
    # end = datetime.datetime.now()
    # start = end - datetime.timedelta(hours=2)
    #
    #
    # print(get_zones(building, hod_client))
    #
    # print(training(building, zone, mdal_client, hod_client,
    #                int(time.mktime(start.timetuple())*1e9),
    #                int(time.mktime(end.timetuple()) * 1e9)))
