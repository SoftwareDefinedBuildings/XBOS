import pymortar
import time
import pytz
import datetime
from rfc3339 import rfc3339
import xbos_services_getter as xbos
import yaml
import sqlite3

pymortar_client = pymortar.Client()

def get_zone_names():

    zones_query = """SELECT ?zone WHERE {
            ?tstat rdf:type brick:Thermostat .
            ?tstat bf:controls/bf:feeds ?zone .
            ?zone rdf:type brick:HVAC_Zone
            };"""

    # zones_query = """SELECT ?zone WHERE {
    #         ?zone rdf:type brick:HVAC_Zone
    #         };"""

    resp = pymortar_client.qualify([zones_query])

    zones_view = pymortar.View(
        name="zones_view",
        sites=resp.sites,
        definition=zones_query,
    )

    request = pymortar.FetchRequest(
        sites=resp.sites,
        views=[
            zones_view
        ]
    )

    zones_data = pymortar_client.fetch(request)

    #print(zones_data)

    print(zones_data.describe_table(viewname='zones_view'))
    #print(zones_data.query("select * from zones_view where zone like '%HVAC%'"))

    return zones_data

def generate_yaml_file(file_path, data):
    with open(file_path, 'w') as outfile:
        yaml.dump(data, outfile)

zones_data = get_zone_names()

query = zones_data.query("select * from zones_view where zone like '%HVAC%'")

data = {}

# print (query)
for _,link, building in query:
    print(link)
    hashIndex = link.index("#")
    zone_name = link[hashIndex + 1:]
    if building in data:
        data[building].append(zone_name)
    else:
        data[building] = [zone_name]

generate_yaml_file("all_zones.yml", data)

# building_stub = xbos.get_building_zone_names_stub()
# buildings = xbos.get_buildings(building_stub)
# zones = xbos.get_all_buildings_zones(building_stub)
# no_data = {}
# no_view = {}

# for building in buildings:
#     for zone in zones[building]:
#         window = "1h"

#         resp = get_indoor_temp_data(building=building, zone=zone, window=window)

#         if resp is None:
#             if building in no_data:
#                 no_data[building].append(zone)
#             else:
#                 no_data[building] = [zone]
#         else:
#             print(building, zone)
#             try:
#                 print("View Len:", len(resp.query('select * from temperature_view')))
#             except sqlite3.OperationalError as e:
#                 print("No View")
#                 if building in no_view:
#                     no_view[building].append(zone)
#                 else:
#                     no_view[building] = [zone]

#     generate_yaml_file("no_view.yml", no_view)
#     generate_yaml_file("no_data.yml", no_data)
