from concurrent import futures
import time
import grpc

import os
import yaml

from pathlib import Path

import building_zone_names_pb2
import building_zone_names_pb2_grpc

_ONE_DAY_IN_SECONDS = 24 * 60 * 60

NAMES_DATA_PATH = Path(os.environ["BUILDING_ZONE_NAMES_DATA_PATH"])
NAMES_HOST_ADDRESS = os.environ["BUILDING_ZONE_NAMES_HOST_ADDRESS"]

def _get_buildings():
    building_path = str(NAMES_DATA_PATH / "all_buildings.yml")

    if os.path.exists(building_path):
        with open(building_path, "r") as f:
            try:
                building_file = yaml.load(f)
            except yaml.YAMLError:
                return None, "yaml could not read file at: %s" % building_path
    else:
        return None, "occupancy file could not be found. path: %s." % building_path

    return building_file, None


def _get_zones(building):
    zone_path = str(NAMES_DATA_PATH / "all_zones.yml")

    if os.path.exists(zone_path):
        with open(zone_path, "r") as f:
            try:
                zone_file = yaml.load(f)
            except yaml.YAMLError:
                return None, "yaml could not read file at: %s" % zone_path
    else:
        return None, "occupancy file could not be found. path: %s." % zone_path

    if building not in zone_file:
        return None, "Zones for given building could not be found."

    return zone_file[building], None


def get_buildings():
    """Returns preprocessed thermal data for a given request or None."""
    print("received building request.")

    buildings, err = _get_buildings()
    if err is not None:
        return None, err

    grpc_buildings = []
    for bldg in buildings:
        grpc_buildings.append(
            building_zone_names_pb2.NamePoint(name=bldg))

    return building_zone_names_pb2.Reply(names=grpc_buildings), None


def get_zones(request):
    """Returns preprocessed thermal data for a given request or None."""

    print("received zone request:", request.building)

    zones, err = _get_zones(request.building)
    if err is not None:
        return None, err

    grpc_zones = []
    for zones in zones:
        grpc_zones.append(
            building_zone_names_pb2.NamePoint(name=zones))

    return building_zone_names_pb2.Reply(names=grpc_zones), None


class BuildingZoneNamesServices(building_zone_names_pb2_grpc.BuildingZoneNamesServicer):
    def __init__(self):
        pass

    def GetBuildings(self, request, context):
        """A simple RPC.

        Sends the outside temperature for a given building, within a duration (start, end), and a requested window
        An error  is returned if there are no temperature for the given request
        """
        buildings, error = get_buildings()
        if buildings is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return building_zone_names_pb2.Reply()
        else:
            return buildings

    def GetZones(self, request, context):
        """A simple RPC.

        Sends the outside temperature for a given building, within a duration (start, end), and a requested window
        An error  is returned if there are no temperature for the given request
        """
        zones, error = get_zones(request)
        if zones is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return building_zone_names_pb2.Reply()
        else:
            return zones


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    building_zone_names_pb2_grpc.add_BuildingZoneNamesServicer_to_server(BuildingZoneNamesServices(), server)
    server.add_insecure_port(NAMES_HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
