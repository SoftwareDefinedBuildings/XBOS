from concurrent import futures
import grpc
import baseline_optimizer_pb2
import baseline_optimizer_pb2_grpc
import time
from datetime import datetime
import pytz
import os
import logging
import xbos_services_getter as xsg
import traceback

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
# BASELINE_OPTIMIZER_HOST_ADDRESS = os.environ["BASELINE_OPTIMIZER_HOST_ADDRESS"]
# TEMPERATURE_BANDS_HOST_ADDRESS = os.environ["TEMPERATURE_BANDS_HOST_ADDRESS"]
# INDOOR_DATA_HISTORICAL_HOST_ADDRESS = os.environ["INDOOR_DATA_HISTORICAL_HOST_ADDRESS"]
# BUILDING_ZONE_NAMES_HOST_ADDRESS = os.environ["BUILDING_ZONE_NAMES_HOST_ADDRESS"]
# OCCUPANCY_HOST_ADDRESS = os.environ["OCCUPANCY_HOST_ADDRESS"]
# INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS = os.environ["INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS"]

BASELINE_OPTIMIZER_HOST_ADDRESS = "localhost:50050"
TEMPERATURE_BANDS_HOST_ADDRESS = "ms.xbos.io:9001"
INDOOR_DATA_HISTORICAL_HOST_ADDRESS = "ms.xbos.io:9001"
BUILDING_ZONE_NAMES_HOST_ADDRESS = "ms.xbos.io:9001"
OCCUPANCY_HOST_ADDRESS = "ms.xbos.io:9001"
INDOOR_TEMPERATURE_PREDICTION_HOST_ADDRESS = "ms.xbos.io:9001"

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def c_to_f(zone_temps,unit):
    if unit == "F":
        return zone_temps
    elif unit == "C":
        new_zone_temps = {}
        for zone in zone_temps:
            new_zone_temps[zone] = (zone_temps[zone]* 9/5.0) + 32
        return new_zone_temps

def f_to_c(zone_temps,unit):
    if unit == "C":
        return zone_temps
    elif unit == "F":
        new_zone_temps = {}
        for zone in zone_temps:
            new_zone_temps[zone] = (zone_temps[zone] - 32 ) * 5/9.0
        return new_zone_temps

def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
       Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0

def verify_temperature_band(starting_temperatures, unit, comfort_band):
    if comfort_band["unit"] == "F":
        starting_temperatures = c_to_f(starting_temperatures,unit)
    elif comfort_band["unit"] == "C":
        starting_temperatures = f_to_c(starting_temperatures,unit)
    else:
        return None, "internal server error, retrieved comfort_bands are not Fahrenheit or Celsius"
    if comfort_band["t_low"] > comfort_band["t_high"]:
        return None, "internal server error, temperature_high is smaller than temperature_low in temperature band"
    return starting_temperatures,None

def verify_request(request,all_buildings,all_zones):
    duration = get_window_in_sec(request.window)
    request_length = [len(request.building),len(request.zones),request.start,request.end,duration,request.unit,request.starting_temperatures]
    if any(v == 0 for v in request_length):
        return "invalid request, empty params"
    if duration <= 0:
        return "invalid request, window is negative or zero"
    if request.building not in all_buildings:
        return "invalid request, building name is not valid."
    if request.start <0 or request.end <0:
        return "invalid request, negative dates"
    if request.start >= request.end:
        return "invalid request, start date is equal or after end date."
    if request.start + (duration * 1e9) > request.end:
        return "invalid request, start date + window is greater than end date"
    if not any([zone not in all_zones[request.building]] for zone in request.zones):
        return "invalid request, invalid zone(s) name"
    if not all([zone in request.starting_temperatures] for zone in request.zones):
        return "invalid request, missing zone temperature(s) in starting_temperatures"
    if request.unit != "F" and request.unit != "C":
        return "invalid request, only Fahrenheit or Celsius temperatures are supported"
    return None

def get_action(starting_temperatures,comfort_band):
    if starting_temperatures <= comfort_band["t_low"]:
        return xsg.HEATING_ACTION
    elif starting_temperatures >= comfort_band["t_high"]:
        return xsg.COOLING_ACTION
    else:
        return xsg.NO_ACTION

def get_normal_schedule_action(request, temperature_bands_stub, occupancy_stub,all_buildings,all_zones):
    logging.info("received request: %s %s %s %s %s %s %s %s %s ",request.building, request.zones, request.start, request.end,request.window,request.starting_temperatures,request.unit, request.occupancy,request.do_not_exceed)
    err = verify_request(request,all_buildings,all_zones)
    if err is not None:
        return None, err

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    actions = {}
    for zone in request.zones:
        if ((request.occupancy and xsg.get_occupancy(occupancy_stub,request.building,zone,d_start,d_end,request.window)["occupancy"].iloc[0]>=0.5) or (not request.occupancy and not request.do_not_exceed)):
            comfort_band = xsg.get_comfortband(temperature_bands_stub,request.building,zone,d_start,d_end,request.window).iloc[0]
        else:
            comfort_band = xsg.get_do_not_exceed(temperature_bands_stub,request.building,zone,d_start,d_end,request.window).iloc[0]

        request.starting_temperatures[zone],err = verify_temperature_band(request.starting_temperatures[zone],request.unit,comfort_band)
        if err is not None:
            return baseline_optimizer_pb2.Reply(), err
        actions[zone] = get_action(request.starting_temperatures[zone],comfort_band)
    return baseline_optimizer_pb2.Reply(actions=actions),None

def get_setpoint_expansion_action(request, temperature_bands_stub, occupancy_stub,all_buildings,all_zones):
    logging.info("received request: %s %s %s %s %s %s %s %s %s %s ",request.building, request.zones, request.start, request.end,request.window,request.starting_temperatures,request.expansion_degrees,request.unit, request.occupancy,request.do_not_exceed)
    err = verify_request(request,all_buildings,all_zones)
    if err is not None:
        return None, err
    if not all([zone in request.expansion_degrees] for zone in request.zones):
        return None, "invalid request, missing zone temperature expansion(s) in expansion_degrees"
    for zone in request.expansion_degrees:
        if request.expansion_degrees[zone] < 0:
            return None, "invalid request, expansion_degrees has negative values"

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    actions = {}
    for zone in request.zones:
        if ((request.occupancy and xsg.get_occupancy(occupancy_stub,request.building,zone,d_start,d_end,request.window)["occupancy"].iloc[0]>=0.5) or (not request.occupancy and not request.do_not_exceed)):
            comfort_band = xsg.get_comfortband(temperature_bands_stub,request.building,zone,d_start,d_end,request.window).iloc[0]
            comfort_band["t_low"] = comfort_band["t_low"] - request.expansion_degrees[zone]/2.0
            comfort_band["t_high"] = comfort_band["t_high"] + request.expansion_degrees[zone]/2.0
        else:
            comfort_band = xsg.get_do_not_exceed(temperature_bands_stub,request.building,zone,d_start,d_end,request.window).iloc[0]

        request.starting_temperatures[zone],err = verify_temperature_band(request.starting_temperatures[zone],request.unit,comfort_band)
        if err is not None:
            return baseline_optimizer_pb2.Reply(), err
        actions[zone] = get_action(request.starting_temperatures[zone],comfort_band)
    return baseline_optimizer_pb2.Reply(actions=actions),None

def get_demand_charge_action(request, temperature_bands_stub, occupancy_stub,all_buildings,all_zones):
    logging.info("received request: %s %s %s %s %s %s %s %s %s %s %s ",request.building, request.zones, request.start, request.end,request.window,request.starting_temperatures,request.unit,request.max_zones,request.include_all_zones, request.occupancy,request.do_not_exceed)
    err = verify_request(request,all_buildings,all_zones)
    if err is not None:
        return None, err
    if request.include_all_zones:
        if not all([zone in request.zones] for zone in all_zones[request.building]):
            return None, "invalid request, missing zone(s) in zones, need all zones"
    if request.max_zones < 0 or request.max_zones > len(request.zones):
        return None, "invalid request, max_zones is less than zero or greater than number of all zones"

    d_start = datetime.utcfromtimestamp(float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    d_end = datetime.utcfromtimestamp(float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    actions = {}
    # get zones that must be controlled because they are outside of the do not exceed limit
    if request.do_not_exceed:
        for zone in request.zones:
            comfort_band = xsg.get_do_not_exceed(temperature_bands_stub,request.building,zone,d_start,d_end,request.window).iloc[0]
            request.starting_temperatures[zone],err = verify_temperature_band(request.starting_temperatures[zone],request.unit,comfort_band)
            if err is not None:
                return baseline_optimizer_pb2.Reply(), err
            actions[zone] = get_action(request.starting_temperatures[zone],comfort_band)
            if actions[zone] != xsg.NO_ACTION:
                request.max_zones -=1

        # if the max_zones <= than zones outside of do not exceed then do not proceed
        if request.max_zones <= 0:
            return baseline_optimizer_pb2.Reply(actions=actions),None

    # calculate discomfort for remaining zones
    discomfort = {}
    comfort_bands = {}
    for zone in request.zones:
        if (zone in actions and actions[zone] == xsg.NO_ACTION) or not request.do_not_exceed:
            occupancy = xsg.get_occupancy(occupancy_stub,request.building,zone,d_start,d_end,request.window)["occupancy"].iloc[0]
            if not (0 <= occupancy <= 1):
                return baseline_optimizer_pb2.Reply(), "internal server error, retrieved occupancy is not between 0 and 1"
            comfort_band = xsg.get_comfortband(temperature_bands_stub,request.building,zone,d_start,d_end,request.window).iloc[0]

            request.starting_temperatures[zone],err = verify_temperature_band(request.starting_temperatures[zone],request.unit,comfort_band)
            if err is not None:
                return baseline_optimizer_pb2.Reply(), err

            discomfort[zone] = max(comfort_band["t_low"] - request.starting_temperatures[zone],request.starting_temperatures[zone] - comfort_band["t_high"],0)
            if request.occupancy:
                discomfort[zone] *= occupancy
            comfort_bands[zone] = comfort_band

    # update actions
    for zone in sorted(discomfort, key=discomfort.__getitem__, reverse=True)[:request.max_zones]:
        actions[zone] = get_action(request.starting_temperatures[zone],comfort_bands[zone])
    for zone in sorted(discomfort, key=discomfort.__getitem__, reverse=True)[request.max_zones:]:
        actions[zone] = xsg.NO_ACTION


    return baseline_optimizer_pb2.Reply(actions=actions),None


def get_normal_schedule_simulation(request, temperature_bands_stub, all_buildings,all_zones):
    pass
def get_setpoint_expansion_simulation(request, temperature_bands_stub,all_buildings,all_zones):
    pass
def get_demand_charge_simulation(request, temperature_bands_stub, all_buildings,all_zones):
    pass

class BaselineOptimizerServicer(baseline_optimizer_pb2_grpc.BaselineOptimizerServicer):
    def __init__(self):
        self.temperature_bands_stub = xsg.get_temperature_band_stub(TEMPERATURE_BANDS_HOST_ADDRESS)
        self.occupancy_stub = xsg.get_occupancy_stub(OCCUPANCY_HOST_ADDRESS)
        building_zone_names_stub = xsg.get_building_zone_names_stub(BUILDING_ZONE_NAMES_HOST_ADDRESS)
        self.supported_buildings = xsg.get_buildings(building_zone_names_stub)
        self.supported_zones = {}
        for bldg in self.supported_buildings:
            self.supported_zones[bldg] = xsg.get_zones(building_zone_names_stub, bldg)

    def GetNormalScheduleAction(self, request, context):
        try:
            actions, error = get_normal_schedule_action(request, self.temperature_bands_stub,self.occupancy_stub, self.supported_buildings,self.supported_zones)
            if actions is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return baseline_optimizer_pb2.Reply()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return actions
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return baseline_optimizer_pb2.Reply()

    def GetSetpointExpansionAction(self, request, context):
        try:
            actions, error = get_setpoint_expansion_action(request, self.temperature_bands_stub, self.occupancy_stub,self.supported_buildings,self.supported_zones)
            if actions is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return baseline_optimizer_pb2.Reply()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return actions
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return baseline_optimizer_pb2.Reply()

    def GetDemandChargeAction(self, request, context):
        try:
            actions, error = get_demand_charge_action(request, self.temperature_bands_stub, self.occupancy_stub,self.supported_buildings,self.supported_zones)
            if actions is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return baseline_optimizer_pb2.Reply()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return actions
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return baseline_optimizer_pb2.Reply()




def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    baseline_optimizer_pb2_grpc.add_BaselineOptimizerServicer_to_server(BaselineOptimizerServicer(), server)
    server.add_insecure_port(BASELINE_OPTIMIZER_HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
