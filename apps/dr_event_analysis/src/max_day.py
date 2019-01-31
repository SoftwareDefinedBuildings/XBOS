import dataclient
m = dataclient.MDALClient("corbusier.cs.berkeley.edu:8088")

def get_max_temp_day(start_day, end_day, site, agg='MAX', offset=0):
    request = {
        "Variables": {
                "weather": {
                    "Definition": """SELECT ?t ?t_uuid FROM %s WHERE {
                        ?t rdf:type/rdfs:subClassOf* brick:Weather_Temperature_Sensor .
                        ?t bf:uuid ?t_uuid
                    };""" % site,
                }
            }   
        }
    request['Composition'] = ['weather']
    request['Aggregation'] = {'weather': [agg]}
    request['Time'] = {
        'Start': start_day,
        'End': end_day,
        'Window': '24h',
        'Aligned': True
    }
    esp_weather = m.query(request)
    df = esp_weather.df
    mean = df.mean(axis=1)
    sorted_days = mean.sort_values(ascending=False)
    print(offset)
    return sorted_days.index[offset]