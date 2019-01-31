import dataclient
m = dataclient.MDALClient("corbusier.cs.berkeley.edu:8088")

def get_weather_power_tstat(site, start, end):
    request = {
        "Variables": {
            "greenbutton": {
                "Definition": """SELECT ?meter ?meter_uuid FROM %s WHERE {
                    ?meter rdf:type brick:Green_Button_Meter .
                    ?meter bf:uuid ?meter_uuid
                };""" % site,
            },
            "weather": {
                "Definition": """SELECT ?t ?t_uuid FROM %s WHERE {
                    ?t rdf:type/rdfs:subClassOf* brick:Weather_Temperature_Sensor .
                    ?t bf:uuid ?t_uuid
                };""" % site,
            },
            "tstat_state": {
                "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                    ?t rdf:type/rdfs:subClassOf* brick:Thermostat_Status .
                    ?t bf:uuid ?t_uuid
                    ?t bf:isPointOf ?tstat .
                    ?tstat rdf:type brick:Thermostat
                };""" % site,
            },
            "tstat_hsp": {
                "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                    ?t rdf:type/rdfs:subClassOf* brick:Supply_Air_Temperature_Heating_Setpoint .
                    ?t bf:uuid ?t_uuid .
                    ?t bf:isPointOf ?tstat .
                    ?tstat rdf:type brick:Thermostat
                };""" % site,
            },
            "tstat_csp": {
                "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                    ?t rdf:type/rdfs:subClassOf* brick:Supply_Air_Temperature_Cooling_Setpoint .
                    ?t bf:uuid ?t_uuid .
                    ?t bf:isPointOf ?tstat .
                    ?tstat rdf:type brick:Thermostat
                };""" % site,
            },
            "tstat_temp": {
                "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                    ?t rdf:type/rdfs:subClassOf* brick:Temperature_Sensor .
                    ?t bf:uuid ?t_uuid .
                    ?t bf:isPointOf ?tstat .
                    ?tstat rdf:type brick:Thermostat
                };""" % site,
            },
        },
    }

    # outside air temp
    request['Composition'] = ['weather']
    request['Aggregation'] = {'weather': ['MEAN']}
    request['Time'] = {
        'Start': start,
        'End': end,
        'Window': '15m',
        'Aligned': True
    }
    resp_weather = m.query(request)

    # power
    request['Composition'] = ['greenbutton']
    request['Aggregation'] = {'greenbutton': ['MEAN']}
    resp_power = m.query(request)

    # tstat temperature
    request['Composition'] = ['tstat_temp', 'tstat_hsp', 'tstat_csp']
    request['Aggregation'] = {'tstat_temp': ['MEAN']}
    resp_temp  = m.query(request)

    # tstat heat setpoint
    request['Composition'] = ['tstat_hsp']
    request['Aggregation'] = {'tstat_hsp': ['MAX']}
    resp_hsp = m.query(request)

    # tstat cool setpoint
    request['Composition'] = ['tstat_csp']
    request['Aggregation'] = {'tstat_csp': ['MAX']}
    resp_csp = m.query(request)

    return {
        'weather': resp_weather,
        'power': resp_power,
        'temperature': resp_temp, 
        'heat setpoint': resp_hsp,
        'cool setpoint': resp_csp
    }
#TODO: group by context
