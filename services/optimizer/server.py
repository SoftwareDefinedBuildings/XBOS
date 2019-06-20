from concurrent import futures
import time
import grpc
import logging
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.DEBUG)

import os
OPTIMIZER_HOST_ADDRESS = os.environ["OPTIMIZER_HOST_ADDRESS"]
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

import os, sys
from datetime import datetime
import pytz

from Optimizers.MPC.MPC import MPC
from Simulation.Simulation import SimulationMPC
import xbos_services_getter as xsg
from Thermostat import Tstat

from xbos_services_getter import optimizer_pb2
from xbos_services_getter import optimizer_pb2_grpc


def get_actions(request,all_buildings,all_zones):
    """Returns temperatures for a given request or None.
    Guarantees that no Nan values in returned data exist."""
    logging.info("received request:", request.building, request.zones,
          request.start, request.end, request.window, request.lambda_val, request.starting_temperatures, request.unit)

    duration = xsg.get_window_in_sec(request.window)

    request_length = [len(request.building), len(request.zones), request.start, request.end,
                      len(request.starting_temperatures), duration]

    if request.building not in all_buildings:
        return None, "invalid request, building name is not valid."
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
    if not all([iter_zone in request.starting_temperatures for iter_zone in all_zones[request.building]]):
        return None, "invalid request, missing zones in starting_temperatures."

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    MPC_instance = MPC(request.building, request.zones, d_start, d_end, request.window, request.lambda_val)
    actions, err = MPC_instance.advise(request.starting_temperatures)
    if actions is None:
        return None, err

    return optimizer_pb2.Reply(actions=actions), None


def get_simulation(request,all_buildings,all_zones):
    """Returns simulation temperatures and actions."""
    print("received request:", request.building, request.zones,
          request.start, request.end, request.window, request.forecasting_horizon,
          request.lambda_val, request.starting_temperatures, request.unit, request.num_runs)

    duration = xsg.get_window_in_sec(request.window)
    forecasting_horizon = xsg.get_window_in_sec(request.forecasting_horizon)

    request_length = [len(request.building), len(request.zones), request.start, request.end,
                      len(request.starting_temperatures), duration]

    if request.building not in all_buildings:
        return None, "invalid request, building name is not valid."
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
    if request.start + (forecasting_horizon * 1e9) > request.end:
        return None, "invalid request, start date + forecasting_horizon is greater than end date."
    if request.unit != "F":
        return None, "invalid request, only Fahrenheit is supported as a unit."
    if not 0 <= request.lambda_val <= 1:
        return None, "invalid request, lambda_val needs to be between 0 and 1."
    if not all([iter_zone in request.starting_temperatures for iter_zone in all_zones[request.building]]):
        return None, "invalid request, missing zones in starting_temperatures."

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    if request.num_runs != 1:
        return None, "invalid request, NotImplementedError: variables num_runs not working. Set num_runs to 1."


    # somewhat inefficient since this could be stored as class var...
    tstats = {iter_zone: Tstat(request.building, iter_zone, request.starting_temperatures[iter_zone],  suppress_not_enough_data_error=True) for iter_zone in request.zones}

    Simulation_instance = SimulationMPC(request.building, request.zones, request.lambda_val,
                                        d_start, d_end, request.forecasting_horizon, request.window, tstats)

    Simulation_instance.run()
    actions = Simulation_instance.actions
    temperatures = Simulation_instance.temperatures

    if actions is None or temperatures is None:
        return None, "Unable to Simulate. Simulation returns None."

    print(actions)
    actions = {iter_zone: optimizer_pb2.ActionList(actions=actions[iter_zone]) for iter_zone in request.zones}
    temperatures = {iter_zone: optimizer_pb2.TemperatureList(temperatures=temperatures[iter_zone]) for iter_zone in request.zones}


    return optimizer_pb2.SimulationReply(simulation_results=[optimizer_pb2.ActionTemperatureReply(actions=actions, temperatures=temperatures)]), None


class OptimizerServicer(optimizer_pb2_grpc.OptimizerServicer):
    def __init__(self):
        building_zone_names_stub = xsg.get_building_zone_names_stub()
        self.supported_buildings = xsg.get_buildings(building_zone_names_stub)
        self.supported_zones = {}
        for bldg in self.supported_buildings:
            self.supported_zones[bldg] = xsg.get_zones(building_zone_names_stub, bldg)

    def GetMPCOptimization(self, request, context):
        actions, error = get_actions(request,self.supported_buildings,self.supported_zones)
        if actions is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return optimizer_pb2.Reply()
        else:
            return actions

    def GetMPCSimulation(self, request, context):
        simulation_response, error = get_simulation(request, self.supported_buildings, self.supported_zones)
        if simulation_response is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return optimizer_pb2.Reply()
        else:
            return simulation_response


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    optimizer_pb2_grpc.add_OptimizerServicer_to_server(OptimizerServicer(), server)
    server.add_insecure_port(OPTIMIZER_HOST_ADDRESS)
    logging.info("Serving on {0}".format(OPTIMIZER_HOST_ADDRESS))
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
