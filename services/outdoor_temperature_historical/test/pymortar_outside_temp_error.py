import pymortar
import time
import pytz
import datetime
from rfc3339 import rfc3339
import xbos_services_getter as xbos

pymortar_client = pymortar.Client()

def get_outside_temp_data(building):

    interval = 3600

    outside_temperature_query = """SELECT ?temp WHERE {
        ?temp rdf:type brick:Weather_Temperature_Sensor .
    };"""

    weather_stations_view = pymortar.View(
        name="weather_stations_view",
        sites=[building],
        definition=outside_temperature_query,
    )

    weather_stations_stream = pymortar.DataFrame(
        name="weather_stations",
        aggregation=pymortar.MEAN,
        window=str(int(interval)) + 's',
        timeseries=[
            pymortar.Timeseries(
                view="weather_stations_view",
                dataVars=["?temp"],
            )
        ]
    )

    weather_stations_time_params = pymortar.TimeParams(
        start=rfc3339(start),
        end=rfc3339(end),
    )

    request = pymortar.FetchRequest(
        sites=[building],
        views=[
            weather_stations_view
        ],
        dataFrames=[
            weather_stations_stream
        ],
        time=weather_stations_time_params
    )

    df = outside_temperature_data = pymortar_client.fetch(request)['weather_stations']

    return df


#This query doesn't return any data for "hayward-station-1", but returns data for all other buildings
end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
start = end - datetime.timedelta(days=10)

for building in xbos.get_buildings(xbos.get_building_zone_names_stub()):
    #Looping through all buildings and getting response
    df = get_outside_temp_data(building)
    if df is None:
        print(building) #The only building that doesn't return data is "hayward-station-1"
    