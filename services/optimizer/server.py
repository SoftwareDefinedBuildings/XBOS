from concurrent import futures
import time
import grpc
import optimizer_pb2
import optimizer_pb2_grpc

import os
OPTIMIZER_HOST_ADDRESS = os.environ["OPTIMIZER_HOST_ADDRESS"]
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

import os, sys
from datetime import datetime
import pytz

from Optimizers.MPC import MPC
import xbos_services_getter as xsg


def get_actions(request):
    """Returns temperatures for a given request or None.
    Guarantees that no Nan values in returned data exist."""
    print("received request:", request.building, request.zones,
          request.start, request.end, request.window, request.lambda_val, request.starting_temperatures, request.unit)

    duration = xsg.get_window_in_sec(request.window)

    request_length = [len(request.building), len(request.zones), request.start, request.end,
                      len(request.starting_temperatures), duration]

    building_zone_names_stub = xsg.get_building_zone_names_stub()
    all_buildings = xsg.get_buildings(building_zone_names_stub)
    if request.building not in all_buildings:
        return None, "invalid request, building name is not valid."
    all_zones = xsg.get_zones(building_zone_names_stub, request.building)

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if request.end > int(time.time() * 1e9):
        return None, "invalid request, end date is in the future."
    if request.start >= request.end:
        return None, "invalid request, start date is after end date."
    if request.start < 0 or request.end < 0:
        return None, "invalid request, negative dates."
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date."
    if request.unit != "F":
        return None, "invalid request, only Fahrenheit is supported as a unit."
    if not 0 <= request.lambda_val <= 1:
        return None, "invalid request, lambda_val needs to be between 0 and 1."
    if not all([iter_zone in request.starting_temperatures for iter_zone in all_zones]):
        return None, "invalid request, missing zones in starting_temperatures."

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    MPC_instance = MPC(request.building, request.zones, d_start, d_end, request.window, request.lambda_val)
    actions, err = MPC_instance.advise(request.starting_temperatures)
    if actions is None:
        return None, err

    return optimizer_pb2.Reply(actions=actions), None


class OptimizerServicer(optimizer_pb2_grpc.OptimizerServicer):
    def __init__(self):
        pass

    def GetMPCOptimization(self, request, context):
        actions, error = get_actions(request)
        if actions is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return optimizer_pb2.Reply()
        else:
            return actions


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    optimizer_pb2_grpc.add_OptimizerServicer_to_server(OptimizerServicer(), server)
    server.add_insecure_port(OPTIMIZER_HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
