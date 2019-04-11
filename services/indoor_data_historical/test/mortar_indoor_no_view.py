import pymortar
import time
import pytz
import datetime
from rfc3339 import rfc3339
import xbos_services_getter as xbos
import yaml
import sqlite3

pymortar_client = pymortar.Client()

def get_indoor_temp_data(building, zone, window):
    start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
    end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
    start = datetime.datetime.utcfromtimestamp(float(start / 1e9)).replace(tzinfo=pytz.utc)
    end = datetime.datetime.utcfromtimestamp(float(end / 1e9)).replace(tzinfo=pytz.utc)

    temperature_query = """SELECT ?tstat ?temp WHERE {
                    ?tstat rdf:type brick:Thermostat .
                    ?tstat bf:controls/bf:feeds <http://xbos.io/ontologies/%s#%s> .
                    ?tstat bf:hasPoint ?temp .
                    ?temp  rdf:type brick:Temperature_Sensor  .
                };""" % (building, zone)

    #resp = pymortar_client.qualify([temperature_query]) Need to get list of all sites

    temperature_view = pymortar.View(
        name="temperature_view",
        sites=[building],
        definition=temperature_query,
    )

    temperature_stream = pymortar.DataFrame(
        name="temperature",
        aggregation=pymortar.MEAN,
        window=window,
        timeseries=[
            pymortar.Timeseries(
                view="temperature_view",
                dataVars=["?temp"],
            )
        ]
    )

    request = pymortar.FetchRequest(
        sites=[building],
        views=[
            temperature_view
        ],
        dataFrames=[
            temperature_stream
        ],
        time=pymortar.TimeParams(
            start=rfc3339(start),
            end=rfc3339(end),
        )
    )

    temperature_data = pymortar_client.fetch(request)

    print(temperature_data["temperature"])

    return temperature_data

def generate_yaml_file(file_path, data):
    with open(file_path, 'w') as outfile:
        yaml.dump(data, outfile)

building_stub = xbos.get_building_zone_names_stub()
buildings = xbos.get_buildings(building_stub)
zones = xbos.get_all_buildings_zones(building_stub)
no_data = {}
no_view = {}

for building in buildings:
    for zone in zones[building]:
        window = "1h"

        resp = get_indoor_temp_data(building=building, zone=zone, window=window)

        if resp is None:
            if building in no_data:
                no_data[building].append(zone)
            else:
                no_data[building] = [zone]
        else:
            print(building, zone)
            try:
                print("View Len:", len(resp.query('select * from temperature_view')))
            except sqlite3.OperationalError as e:
                print("No View")
                if building in no_view:
                    no_view[building].append(zone)
                else:
                    no_view[building] = [zone]
    
    generate_yaml_file("no_view.yml", no_view)
    generate_yaml_file("no_data.yml", no_data)

