from concurrent import futures
import time
import grpc
import hvac_consumption_pb2
import hvac_consumption_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

import os
HVAC_CONSUMPTION_PATH = os.environ["HVAC_CONSUMPTION_PATH"]

import yaml
import numpy as np


def _get_hvac_consumption_config(building, zone):
    consumption_path = HVAC_CONSUMPTION_PATH + "/" + building + "/" + zone + ".yml"

    if os.path.exists(consumption_path):
        with open(consumption_path, "r") as f:
            try:
                consumption_config = yaml.load(f)
            except yaml.YAMLError:
                return None, "yaml could not read file at: %s" % consumption_path
    else:
        return None, "consumption file could not be found. path: %s." % consumption_path

    return consumption_config, None


def get_hvac_consumption(request):
    """Returns the consumption of heating/cooling actions in the given HVAC zone or None if Error encountered."""

    print("received request:", request.building, request.zone)

    request_length = [len(request.building), len(request.zone)]

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"

    consumption_config, err = _get_hvac_consumption_config(request.building, request.zone)

    if consumption_config is None:
        return None, err

    if consumption_config["heating_consumption_stage_two"] is None:
        heating_consumption_stage_two = np.nan
    else:
        heating_consumption_stage_two = consumption_config["heating_consumption_stage_two"]
    if consumption_config["cooling_consumption_stage_two"] is None:
        cooling_consumption_stage_two = np.nan
    else:
        cooling_consumption_stage_two = consumption_config["cooling_consumption_stage_two"]

    return hvac_consumption_pb2.ConsumptionPoint(
        heating_consumption=consumption_config["heating_consumption"],
        cooling_consumption=consumption_config["cooling_consumption"],
        ventilation_consumption=consumption_config["ventilation_consumption"],
        heating_consumption_stage_two=heating_consumption_stage_two,
        cooling_consumption_stage_two=cooling_consumption_stage_two,
        unit="kWh"), None


class ConsumptionHVACServicer(hvac_consumption_pb2_grpc.ConsumptionHVACServicer):
    def __init__(self):
        pass

    def GetConsumption(self, request, context):
        """A simple RPC.

        Sends the hvac_consumption for a given building.
        An error  is returned if hvac_consumption could not be loaded.
        """
        hvac_consumption, error = get_hvac_consumption(request)
        if hvac_consumption is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return hvac_consumption_pb2.ConsumptionPoint()
        else:
            return hvac_consumption


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hvac_consumption_pb2_grpc.add_ConsumptionHVACServicer_to_server(ConsumptionHVACServicer(), server)
    server.add_insecure_port('[::]:50056')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()





