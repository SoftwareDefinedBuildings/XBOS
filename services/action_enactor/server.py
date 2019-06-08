from concurrent import futures
import grpc
import action_enactor_pb2
import action_enactor_pb2_grpc
import time
import os
import sys

import logging
import traceback

from xbos.services.hod import HodClient
from xbos import get_client
from xbos.devices.thermostat import Thermostat


_ONE_DAY_IN_SECONDS = 60 * 60 * 24
ACTION_ENACTOR_HOST_ADDRESS = os.environ["ACTION_ENACTOR_HOST_ADDRESS"]
'''
Utility constants state and mode
'''
NO_ACTION = 0
HEATING_ACTION = 1
COOLING_ACTION = 2
FAN = 3
TWO_STAGE_HEATING_ACTION = 4
TWO_STAGE_COOLING_ACTION = 5
# MODES
OFF = 0
HEAT_ONLY = 1
COOL_ONLY = 2
AUTO = 3

xsg_all_buildings = ['avenal-recreation-center', 'berkeley-corporate-yard', 'csu-dominguez-hills', 'word-of-faith-cc', 'hayward-station-1', 'avenal-public-works-yard', 'local-butcher-shop', 'avenal-veterans-hall', 'south-berkeley-senior-center', 'orinda-community-center', 'jesse-turner-center', 'avenal-animal-shelter', 'north-berkeley-senior-center', 'avenal-movie-theatre', 'hayward-station-8', 'ciee']
# xsg_all_buildings = ['avenal-veterans-hall']

xsg_all_zones = {'avenal-recreation-center': ['hvac_zone_large_room', 'hvac_zone_tech_center'], 'berkeley-corporate-yard': ['hvac_zone_parks_assembly', 'hvac_zone_radioshop', 'hvac_zone_s_and_u_open_office', 'hvac_zone_scott_britt_rm', 'hvac_zone_cs_open_office', 'hvac_zone_electricalshop', 'hvac_zone_fac_main_dept', 'hvac_zone_green_room'], 'csu-dominguez-hills': ['hvac_zone_sac_2101', 'hvac_zone_sac_2114', 'hvac_zone_sac_2150', 'hvac_zone_sac_2126', 'hvac_zone_sac_2113a', 'hvac_zone_sac_2104', 'hvac_zone_sac_2_corridor', 'hvac_zone_sac_2106', 'hvac_zone_sac_2129', 'hvac_zone_sac_2107', 'hvac_zone_sac_2113', 'hvac_zone_sac_2149', 'hvac_zone_sac_2102', 'hvac_zone_sac_2103', 'hvac_zone_sac_2144', 'hvac_zone_sac_2105', 'hvac_zone_sac_2134'], 'word-of-faith-cc': ['hvac_zone_hospitality', 'hvac_zone_fellowship_hall', 'hvac_zone_lobby', 'hvac_zone_sanctuary_lb_2', 'hvac_zone_sanctuary_rf_2', 'hvac_zone_school_age_rm', 'hvac_zone_pre_k_classroom'], 'hayward-station-1': ['hvac_zone_ac_2', 'hvac_zone_ac_3', 'hvac_zone_ac_4', 'hvac_zone_ac_5', 'hvac_zone_ac_6', 'hvac_zone_ac_7', 'hvac_zone_ac_1'], 'avenal-public-works-yard': ['hvac_zone_public_works'], 'local-butcher-shop': ['hvac_zone_retail_space'], 'avenal-veterans-hall': ['hvac_zone_ac_3', 'hvac_zone_ac_1', 'hvac_zone_ac_4', 'hvac_zone_ac_6', 'hvac_zone_ac_5', 'hvac_zone_ac_2'], 'south-berkeley-senior-center': ['hvac_zone_ac_2', 'hvac_zone_ac_3', 'hvac_zone_front_office'], 'orinda-community-center': ['hvac_zone_ac_7', 'hvac_zone_rm7', 'hvac_zone_kinder_gym', 'hvac_zone_ac_6', 'hvac_zone_ac_3', 'hvac_zone_rm1', 'hvac_zone_ac_4', 'hvac_zone_ac_5', 'hvac_zone_rm6', 'hvac_zone_ac_1', 'hvac_zone_front_office', 'hvac_zone_ac_2', 'hvac_zone_rm2', 'hvac_zone_ac_8'], 'jesse-turner-center': ['hvac_zone_resource_center', 'hvac_zone_class_132', 'hvac_zone_meeting_room_122', 'hvac_zone_multi_purpose_147', 'hvac_zone_fitness_room_138', 'hvac_zone_assembly_112', 'hvac_zone_basketball_court_2', 'hvac_zone_basketball_court_6', 'hvac_zone_basketball_court_5', 'hvac_zone_lobby', 'hvac_zone_basketball_court_3', 'hvac_zone_control_desk', 'hvac_zone_foyer_gallery', 'hvac_zone_assembly_113', 'hvac_zone_class_131', 'hvac_zone_front_entrance', 'hvac_zone_office_room_148', 'hvac_zone_basketball_court_4', 'hvac_zone_dance_room_109', 'hvac_zone_back_stage', 'hvac_zone_basketball_court_1', 'hvac_zone_kitchen', 'hvac_zone_assembly_111', 'hvac_zone_electrical_room123'], 'avenal-animal-shelter': ['hvac_zone_shelter_corridor'], 'north-berkeley-senior-center': ['hvac_zone_ac_1', 'hvac_zone_ac_3', 'hvac_zone_ac_5'], 'avenal-movie-theatre': ['hvac_zone_lobby', 'hvac_zone_main_hallway', 'hvac_zone_room_a', 'hvac_zone_theater_2', 'hvac_zone_back_hallway', 'hvac_zone_room_d', 'hvac_zone_pegasus_hall', 'hvac_zone_theater_1'], 'hayward-station-8': ['hvac_zone_f_3', 'hvac_zone_f_1', 'hvac_zone_f_2'], 'ciee': ['hvac_zone_centralzone', 'hvac_zone_eastzone', 'hvac_zone_northzone', 'hvac_zone_southzone']}

hod_xsg_mismatch = {"csu-dominguez-hills":{
                "hvac_zone_sac-2104":"hvac_zone_sac_2104",
                "hvac_zone_sac-2106":"hvac_zone_sac_2106",
                "hvac_zone_sac-2102":"hvac_zone_sac_2102"},
            "hayward-station-1":{
                "hvac_zone_ac-2":'hvac_zone_ac_2',
                "hvac_zone_ac-3":'hvac_zone_ac_3',
                "hvac_zone_ac-4":'hvac_zone_ac_4',
                "hvac_zone_ac-5":'hvac_zone_ac_5',
                "hvac_zone_ac-6":'hvac_zone_ac_6',
                "hvac_zone_ac-7":'hvac_zone_ac_7',
                "hvac_zone_ac-1":'hvac_zone_ac_1'},
            "avenal-veterans-hall":{
                "hvac_zone_ac-3":'hvac_zone_ac_3',
                "hvac_zone_ac-1":'hvac_zone_ac_1',
                "hvac_zone_ac-4":'hvac_zone_ac_4',
                "hvac_zone_ac-6":'hvac_zone_ac_6',
                "hvac_zone_ac-5":'hvac_zone_ac_5',
                "hvac_zone_ac-2":'hvac_zone_ac_2'},
            "south-berkeley-senior-center":{
                "hvac_zone_ac-2":"hvac_zone_ac_2",
                "hvac_zone_ac-3":"hvac_zone_ac_3"},
            "orinda-community-center":{
                "hvac_zone_ac-7":'hvac_zone_ac_7',
                "hvac_zone_ac-6":'hvac_zone_ac_6',
                "hvac_zone_ac-3":'hvac_zone_ac_3',
                "hvac_zone_ac-4":'hvac_zone_ac_4',
                "hvac_zone_ac-5":'hvac_zone_ac_5',
                "hvac_zone_ac-1":'hvac_zone_ac_1',
                "hvac_zone_ac-2":'hvac_zone_ac_2',
                "hvac_zone_ac-8":'hvac_zone_ac_8'},
            "north-berkeley-senior-center":{
                "hvac_zone_ac-1":'hvac_zone_ac_1',
                "hvac_zone_ac-3":'hvac_zone_ac_3',
                "hvac_zone_ac-5":'hvac_zone_ac_5'},
            "hayward-station-8":{
                "hvac_zone_f-3":"hvac_zone_f_3",
                "hvac_zone_f-1":"hvac_zone_f_1",
                "hvac_zone_f-2":"hvac_zone_f_2"}}

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

def verify_building_zones(request):
    if len(request.building) == 0 or len(request.zones) == 0:
        return "invalid request, empty params"
    if request.building not in xsg_all_buildings:
        return "invalid request, building name is not valid."
    if not set(request.zones).issubset(set(xsg_all_zones[request.building])):
        return "invalid request, invalid zone(s) name"

def get_all_thermostats(client, hod, building):
    """Gets the thermostats for given building.
    :param client: xbos client object
    :param hod: hod client object
    :param building: (string) building name
    :return {zone: tstat object}"""

    query = """SELECT ?uri ?zone FROM %s WHERE {
        ?tstat rdf:type/rdfs:subClassOf* brick:Thermostat .
        ?tstat bf:uri ?uri .
        ?tstat bf:controls/bf:feeds ?zone .
        };"""

    # Start of FIX for missing Brick query
    query = """SELECT ?zone ?uri FROM  %s WHERE {
              ?tstat rdf:type brick:Thermostat .
              ?tstat bf:controls ?RTU .
              ?RTU rdf:type brick:RTU .
              ?RTU bf:feeds ?zone.
              ?zone rdf:type brick:HVAC_Zone .
              ?tstat bf:uri ?uri.
              };"""
    # End of FIX - delete when Brick is fixed
    building_query = query % building

    tstat_query_data = hod.do_query(building_query)['Rows']
    tstats = {}
    for tstat in tstat_query_data:
        k = tstat["?zone"].lower()
        if building in hod_xsg_mismatch:
            if k in hod_xsg_mismatch[building]:
                k = hod_xsg_mismatch[building][k]
        try:
            tstats[k] = Thermostat(client, tstat["?uri"])
        except Exception:
            tb = traceback.format_exc()
            logging.error("failed to get thermostat for bldg:%s, zone:%s\n%s",building,k,tb)

    return tstats

def set_thermostat_state(tstat,state,trials):
    for i in range(trials):
        try:
            tstat.write(state)
            return True
        except:
            continue
    return False

def get_thermostat_state(building, zones, building_tstats):
    zone_current_htgsp = {}
    zone_current_clgsp = {}
    zone_current_override = {}
    zone_current_mode = {}
    zone_current_state = {}
    zone_current_temperature = {}
    for zone in zones:
        zone_current_htgsp[zone] = building_tstats[building][zone].heating_setpoint
        zone_current_clgsp[zone] = building_tstats[building][zone].cooling_setpoint
        zone_current_override[zone] = building_tstats[building][zone].override
        zone_current_mode[zone] = building_tstats[building][zone].mode
        zone_current_state[zone] = building_tstats[building][zone].state
        zone_current_temperature[zone] = building_tstats[building][zone].temperature
        logging.info("zone:%s, htgsp:%s, clgsp:%s, override:%s, mode:%s, state:%s, temp:%s, ",zone,zone_current_htgsp[zone],zone_current_clgsp[zone],zone_current_override[zone] , zone_current_mode[zone],zone_current_state[zone],zone_current_temperature[zone])
    return zone_current_htgsp,zone_current_clgsp,zone_current_override,zone_current_mode,zone_current_state,zone_current_temperature

def turn_thermostat_off(request,building_tstats):
    logging.info("turn_thermostat_off received request: %s %s %s",request.building, request.zones,request.num_trials)
    err = verify_building_zones(request)
    if err is not None:
        return None, err
    if request.num_trials <= 0:
        return None, "invalid request, num_trials is less than or equal zero"
    zone_request_status = {}
    state_off = {"override": False, "mode":OFF}
    for zone in request.zones:
        zone_request_status[zone] = set_thermostat_state(building_tstats[request.building][zone],state_off,request.num_trials)
    zone_current_htgsp,zone_current_clgsp,zone_current_override,zone_current_mode,zone_current_state,zone_current_temperature = get_thermostat_state(request.building, request.zones,building_tstats)
    return action_enactor_pb2.Response(zone_request_status=zone_request_status,unit="F",zone_current_htgsp=zone_current_htgsp,zone_current_clgsp=zone_current_clgsp,zone_current_override=zone_current_override,zone_current_mode=zone_current_mode,zone_current_state=zone_current_state,zone_current_temperature=zone_current_temperature), None

def restore_thermostat_schedule(request,building_tstats):
    logging.info("restore_thermostat_schedule received request: %s %s %s",request.building, request.zones,request.num_trials)
    err = verify_building_zones(request)
    if err is not None:
        return None, err
    if request.num_trials <= 0:
        return None, "invalid request, num_trials is less than or equal zero"
    zone_request_status = {}
    state_resume = {"override": False}
    for zone in request.zones:
        zone_request_status[zone] = set_thermostat_state(building_tstats[request.building][zone],state_resume,request.num_trials)
    zone_current_htgsp,zone_current_clgsp,zone_current_override,zone_current_mode,zone_current_state,zone_current_temperature = get_thermostat_state(request.building, request.zones,building_tstats)
    return action_enactor_pb2.Response(zone_request_status=zone_request_status,unit="F",zone_current_htgsp=zone_current_htgsp,zone_current_clgsp=zone_current_clgsp,zone_current_override=zone_current_override,zone_current_mode=zone_current_mode,zone_current_state=zone_current_state,zone_current_temperature=zone_current_temperature), None

def get_thermostat_status(request,building_tstats):
    logging.info("get_thermostat_status received request: %s %s",request.building, request.zones)
    err = verify_building_zones(request)
    if err is not None:
        return None, err

    zone_current_htgsp,zone_current_clgsp,zone_current_override,zone_current_mode,zone_current_state,zone_current_temperature = get_thermostat_state(request.building, request.zones,building_tstats)
    return action_enactor_pb2.Response(unit="F",zone_current_htgsp=zone_current_htgsp,zone_current_clgsp=zone_current_clgsp,zone_current_override=zone_current_override,zone_current_mode=zone_current_mode,zone_current_state=zone_current_state,zone_current_temperature=zone_current_temperature), None
    # return get_thermostat_state(request.building, request.zones,building_tstats), None

def get_user_overwrite(request,building_tstats):
    logging.info("get_user_overwrite received request: %s %s %s %s %s",request.building, request.zones,request.zone_expected_htgsp, request.zone_expected_clgsp ,request.unit)
    err = verify_building_zones(request)
    if err is not None:
        return None, err
    request_length = [len(request.zone_expected_htgsp),len(request.zone_expected_clgsp),len(request.unit)]
    if any(v == 0 for v in request_length):
        return None,"invalid request, empty params"
    if request.unit != "F":
        return None, "invalid request, only Fahrenheit temperatures are supported"
    if set(request.zones) != set(request.zone_expected_htgsp):
        return None, "invalid request, missing zone temperature(s) in zone_expected_htgsp"
    if set(request.zones) != set(request.zone_expected_clgsp):
        return None, "invalid request, missing zone temperature(s) in zone_expected_clgsp"
    zone_request_status = {}
    for zone in request.zones:
        zone_request_status[zone] = (building_tstats[building][zone].heating_setpoint == request.zone_expected_htgsp) and (building_tstats[building][zone].cooling_setpoint == request.zone_expected_clgsp)
    zone_current_htgsp,zone_current_clgsp,zone_current_override,zone_current_mode,zone_current_state,zone_current_temperature = get_thermostat_state(request.building, request.zones,building_tstats)
    return action_enactor_pb2.Response(zone_request_status=zone_request_status,unit="F",zone_current_htgsp=zone_current_htgsp,zone_current_clgsp=zone_current_clgsp,zone_current_override=zone_current_override,zone_current_mode=zone_current_mode,zone_current_state=zone_current_state,zone_current_temperature=zone_current_temperature), None

def set_thermostat_action(request,building_tstats):
    logging.info("set_thermostat_action received request: %s %s %s %s %s %s",request.building, request.zones,request.zone_action, request.zone_dne_htgsp,request.zone_dne_clgsp, request.zone_hysteresis, request.num_trials ,request.unit)
    err = verify_building_zones(request)
    if err is not None:
        return None, err
    request_length = [len(request.zone_action),len(request.zone_dne_htgsp),len(request.zone_dne_clgsp),len(request.zone_hysteresis),request.num_trials ,len(request.unit)]
    if any(v == 0 for v in request_length):
        return None,"invalid request, empty params"
    if request.unit != "F":
        return None,"invalid request, only Fahrenheit temperatures are supported"
    if request.num_trials <= 0:
        return None, "invalid request, num_trials is less than or equal zero"
    if set(request.zones) != set(request.zone_dne_htgsp):
        return None, "invalid request, missing zone temperature(s) in zone_dne_htgsp"
    if set(request.zones) != set(request.zone_dne_clgsp):
        return None, "invalid request, missing zone temperature(s) in zone_dne_clgsp"
    if set(request.zones) != set(request.zone_hysteresis):
        return None, "invalid request, missing zone temperature(s) in zone_hysteresis"

    zone_request_status = {}
    for zone in request.zones:
        state_setpoint = {}
        if request.zone_dne_clgsp[zone] <= request.zone_dne_htgsp[zone]:
            return None, "invalid request, zone_dne_clgsp is less than zone_dne_htgsp"
        if request.zone_hysteresis[zone] < 0:
            return None, "invalid request, zone_hysteresis cannot be negative"
        if  request.zone_action[zone]==NO_ACTION:
            state_setpoint = {"heating_setpoint": request.zone_dne_htgsp[zone] , "cooling_setpoint": request.zone_dne_clgsp[zone], "override":True, "mode":AUTO}
        elif request.zone_action[zone]==HEATING_ACTION:
            heating_setpoint = building_tstats[request.building][zone].temperature + 2 * request.zone_hysteresis[zone]
            cooling_setpoint = request.zone_dne_clgsp[zone]
            if heating_setpoint < request.zone_dne_htgsp[zone]:
                heating_setpoint = request.zone_dne_htgsp[zone]
            state_setpoint = {"heating_setpoint": heating_setpoint, "cooling_setpoint": cooling_setpoint, "override":True, "mode":AUTO}
        elif request.zone_action[zone]==COOLING_ACTION:
            cooling_setpoint = building_tstats[request.building][zone].temperature - 2 * request.zone_hysteresis[zone]
            heating_setpoint = request.zone_dne_htgsp[zone]
            if cooling_setpoint > request.zone_dne_clgsp[zone]:
                cooling_setpoint = request.zone_dne_clgsp[zone]
            state_setpoint = {"heating_setpoint": heating_setpoint, "cooling_setpoint": cooling_setpoint, "override":True, "mode":AUTO}
        else:
            return None, "invalid request, zone.actions can only be NO_ACTION, HEATING_ACTION, COOLING_ACTION"
        zone_request_status[zone] = set_thermostat_state(building_tstats[request.building][zone],state_setpoint,request.num_trials)
    zone_current_htgsp,zone_current_clgsp,zone_current_override,zone_current_mode,zone_current_state,zone_current_temperature = get_thermostat_state(request.building, request.zones,building_tstats)
    return action_enactor_pb2.Response(zone_request_status=zone_request_status,unit="F",zone_current_htgsp=zone_current_htgsp,zone_current_clgsp=zone_current_clgsp,zone_current_override=zone_current_override,zone_current_mode=zone_current_mode,zone_current_state=zone_current_state,zone_current_temperature=zone_current_temperature), None

def set_thermostat_setpoint(request,building_tstats):
    logging.info("set_thermostat_setpoint received request: %s %s %s %s %s %s",request.building, request.zones,request.zone_htgsp,request.zone_clgsp, request.num_trials ,request.unit)
    err = verify_building_zones(request)
    if err is not None:
        return None, err
    request_length = [len(request.zone_htgsp),len(request.zone_clgsp),request.num_trials ,len(request.unit)]
    if any(v == 0 for v in request_length):
        return None,"invalid request, empty params"
    if request.unit != "F":
        return None,"invalid request, only Fahrenheit temperatures are supported"
    if request.num_trials <= 0:
        return None, "invalid request, num_trials is less than or equal zero"
    if set(request.zones) != set(request.zone_htgsp):
        return None, "invalid request, missing zone temperature(s) in zone_htgsp"
    if set(request.zones) != set(request.zone_clgsp):
        return None, "invalid request, missing zone temperature(s) in zone_clgsp"

    zone_request_status = {}
    for zone in request.zones:
        if request.zone_clgsp[zone] <= request.zone_htgsp[zone]:
            return None, "invalid request, zone_clgsp is less than or equal to zone_htgsp"
        state_setpoint = {"heating_setpoint": request.zone_htgsp[zone], "cooling_setpoint": request.zone_clgsp[zone], "override":True, "mode":AUTO}
        zone_request_status[zone] = set_thermostat_state(building_tstats[request.building][zone],state_setpoint,request.num_trials)
    zone_current_htgsp,zone_current_clgsp,zone_current_override,zone_current_mode,zone_current_state,zone_current_temperature = get_thermostat_state(request.building, request.zones,building_tstats)
    return action_enactor_pb2.Response(zone_request_status=zone_request_status,unit="F",zone_current_htgsp=zone_current_htgsp,zone_current_clgsp=zone_current_clgsp,zone_current_override=zone_current_override,zone_current_mode=zone_current_mode,zone_current_state=zone_current_state,zone_current_temperature=zone_current_temperature), None

class ActionEnactorServicer(action_enactor_pb2_grpc.ActionEnactorServicer):
    def __init__(self):
        # get a bosswave client
        client = get_client() # defaults to $BW2_AGENT, $BW2_DEFAULT_ENTITY

        # Get hod client.
        hod_client = HodClient("xbos/hod", client)

        self.building_tstats = {}
        hod_xsg_match = True
        try:
            for bldg in xsg_all_buildings:
                # Getting the tstats for the building.
                self.building_tstats[bldg] = get_all_thermostats(client, hod_client, bldg)
                if not set(xsg_all_zones[bldg]).issubset(set(self.building_tstats[bldg])):
                    missing_zones = []
                    for zone in xsg_all_zones[bldg]:
                        if zone not in self.building_tstats[bldg]:
                            missing_zones.append(zone)
                    logging.critical("zone mismatch between hod and xbos_services_getter for bldg: %s \nhod_zones:%s\nmissing zones:%s\n",bldg,self.building_tstats[bldg].keys(),missing_zones)
                    hod_xsg_match = False
            if not hod_xsg_match:
                sys.exit(0)
        except Exception:
            tb = traceback.format_exc()
            logging.critical("failed to get thermostats\n%s",tb)
            sys.exit(0)
    def SetThermostatAction(self,request,context):
        try:
            setpoints, error = set_thermostat_action(request,self.building_tstats)
            if setpoints is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return action_enactor_pb2.Response()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return setpoints
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return action_enactor_pb2.Response()

    def SetThermostatSetpoint(self,request,context):
        try:
            setpoints, error = set_thermostat_setpoint(request,self.building_tstats)
            if setpoints is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return action_enactor_pb2.Response()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return setpoints
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return action_enactor_pb2.Response()

    def GetThermostatStatus(self,request,context):
        try:
            setpoints, error = get_thermostat_status(request,self.building_tstats)
            if setpoints is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return action_enactor_pb2.Response()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return setpoints
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return action_enactor_pb2.Response()

    def TurnThermostatOff(self, request,context):
        try:
            setpoints, error = turn_thermostat_off(request,self.building_tstats)
            if setpoints is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return action_enactor_pb2.Response()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return setpoints
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return action_enactor_pb2.Response()

    def GetUserOverwrite(self,request,context):
        try:
            setpoints, error = get_user_overwrite(request,self.building_tstats)
            if setpoints is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return action_enactor_pb2.Response()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return setpoints
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return action_enactor_pb2.Response()

    def RestoreThermostatSchedule(self,request,context):
        try:
            setpoints, error = restore_thermostat_schedule(request,self.building_tstats)
            if setpoints is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return action_enactor_pb2.Response()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return setpoints
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return action_enactor_pb2.Response()



def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    action_enactor_pb2_grpc.add_ActionEnactorServicer_to_server(ActionEnactorServicer(), server)
    server.add_insecure_port(ACTION_ENACTOR_HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
