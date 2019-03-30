#python2.7 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. indoor_temperature_prediction.proto

# getting the utils file here
import os, sys

import datetime
import pytz
import pandas as pd


from concurrent import futures
import time
import grpc

import thermal_model_pb2
import thermal_model_pb2_grpc

import process_indoor_data as pid

_INTERVAL = "5m" # minutes # TODO allow for getting multiples of 5. Prediction horizon.
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

THERMAL_MODELS = {
"orinda-public-library": {},
"orinda-community-center": {},
"hayward-station-1": {},
"hayward-station-8": {},
"avenal-animal-shelter": {},
"avenal-movie-theatre": {},
"avenal-public-works-yard": {},
"avenal-recreation-center": {},
"avenal-veterans-hall": {},
"south-berkeley-senior-center": {},
"north-berkeley-senior-center": {},
"berkeley-corporation-yard": {},
"word-of-faith-cc": {},
"local-butcher-shop": {},
"jesse-turner-center": {},
"ciee": {},
"csu-dominguez-hills": {} }

END = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) # TODO how to make environ var. 
START = END - datetime.timedelta(days=120)

def check_thermal_model(building, zone):
    if building not in THERMAL_MODELS or zone not in THERMAL_MODELS[building]:
        # TODO ERROR CHECK.
        thermal_model, err = training(building, zone, START, END)
        if thermal_model is None:
            return None, err
        THERMAL_MODELS[building][zone] = thermal_model

    return None, None


def training(building, zone, start, end):
    """

    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :return: Trained thermal model object.
    """
    training_data = td.get_training_data(building, zone, start, end, _INTERVAL)
    if training_data is None:
        return None, "Could not get Training Data"

    # train thermal model
    thermal_model = ThermalModel(utils.get_window_in_sec(_INTERVAL)/60)
    thermal_model.fit(training_data, training_data["t_next"])

    return thermal_model, None


def prediction(request):
    """Returns temperature prediction for a given request or None."""

    print("received request:", request.building, request.zone, request.current_time, request.action,
          request.indoor_temperature, request.outside_temperature, request.other_zone_temperatures, request.temperature_unit,
          request.occupancy)

    request_length = [len(request.building), len(request.zone), request.current_time,
          request.indoor_temperature, request.outside_temperature, request.other_zone_temperatures, len(request.temperature_unit)]

    unit = "F"  # fahrenheit for now .

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if not (0 <= request.occupancy <= 1):
        return None, "Occupancy is not between 0 and 1."
    if not (0 <= request.action <=5):
        return None, "Action is not between 0 and 5."

    # TODO Check if valid building/zone/temperature unit/zone, outside and indoor temperature (not none)

    # checking if we have a thermal model, and training if necessary.
    _, err = check_thermal_model(request.building, request.zone)
    if err is not None:
        return None, err
    thermal_model = THERMAL_MODELS[request.building][request.zone]
    data_point = {
        "t_in": request.indoor_temperature,
        "action": request.action,
        "t_out": request.outside_temperature,
        "dt": utils.get_window_in_sec(_INTERVAL) / 60,
        "t_last": request.indoor_temperature  # TODO t_last feature should be added to proto specs
    }

    for iter_zone, iter_temp in request.other_zone_temperatures.items():
        if iter_zone != request.zone:
            data_point["temperature_zone_" + iter_zone] = iter_temp

    prediction = thermal_model.predict(pd.DataFrame([data_point]))
    prediction_reply = thermal_model_pb2.PredictedTemperatureReply(time=int(request.current_time + utils.get_window_in_sec(_INTERVAL) * 1e9),
                                                                temperature=prediction[0],
                                                                 unit=unit)
    return prediction_reply, None


class ThermalModelServicer(thermal_model_pb2_grpc.ThermalModelServicer):
    def __init__(self):
        pass

    def GetPrediction(self, request, context):
        """A simple RPC.

        Sends the outside temperature for a given building, within a duration (start, end), and a requested window
        An error  is returned if there are no temperature for the given request
        """
        predicted_temperature, error = prediction(request)
        if predicted_temperature is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return thermal_model_pb2.PredictedTemperatureReply()
        else:
            return predicted_temperature


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    thermal_model_pb2_grpc.add_ThermalModelServicer_to_server(ThermalModelServicer(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
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
