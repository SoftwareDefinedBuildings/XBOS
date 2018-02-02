import datetime, pytz
import pandas as pd
from scipy.optimize import curve_fit
from datetime import datetime, timedelta
from xbos import get_client
from xbos.services.mdal import *
from xbos.services.pundat import DataClient, make_dataframe
from xbos.services.hod import HodClient
from sklearn.utils import shuffle
from weather_model import predict_day as predict_weather
from dateutil import rrule
from datetime import datetime, timedelta

# data clients
mdal = BOSSWAVEMDALClient("xbos/mdal")
hod = HodClient("xbos/hod")
SITE = "ciee"

# Brick queries
zone_query = """SELECT ?zone FROM %s WHERE {
    ?zone rdf:type brick:HVAC_Zone .
};"""

thermostat_state_query = """SELECT ?tstat_state_uuid FROM %s WHERE {
    ?tstat rdf:type brick:Thermostat .
    ?tstat bf:controls/bf:feeds+ <%s> .
    ?tstat bf:hasPoint ?state .
    ?state rdf:type brick:Thermostat_Status .
    ?state bf:uuid ?tstat_state_uuid
};"""

thermostat_temp_query = """SELECT ?tstat_temp_uuid FROM %s WHERE {
    ?tstat rdf:type brick:Thermostat .
    ?tstat bf:controls/bf:feeds+ <%s> .
    ?tstat bf:hasPoint ?temp .
    ?temp rdf:type brick:Temperature_Sensor .
    ?temp bf:uuid ?tstat_temp_uuid .
};"""

# if state is 1 we are doing heating
def f1(row):
    if row['a'] > 0 and row['a']<=1:
        return 1
    return 0

# if state is 2 we are doing cooling
def f2(row):
    if row['a']>1 and row['a']<=2:
        return 1
    return 0

# WE ARE NOT LEARNING VENTILATION RIGHT NOW
# $T^{IN}_{t+1}= c_1 * a^{H} * T^{IN}_{t} + c_2 * a^{C} * T^{IN}_{t} + c_3 * T^{IN}_{t}$
def func(X, c1, c2, c3, c4):
    Tin, a1, a2, Tout = X
    return c1 * a1 * Tin + c2 * a2 * Tin + c3 * Tin + c4 * (Tout-Tin)#+ c4  * (1-a1)*(1-a2)

def next_temperature(popt, Tin, Tout, action):
    if action == 1:
        return round(func([Tin, 1, 0, Tout], *popt) * 400) / 400.0
    elif action == 2:
        return round(func([Tin, 0, 1, Tout], *popt) * 400) / 400.0
    return round(func([Tin, 0, 0, Tout], *popt) * 400) / 400.0

def execute_schedule(day, sched, popt, initial_temperature):
    """
    sched is a list of (hsp, csp) setpoints at 30m intervals
    """
    output = []
    actions = []
    prev_temp = initial_temperature
    weather = predict_weather(day)
    print len(sched), len(weather)
    for idx, epoch in enumerate(sched):
        if prev_temp < epoch[0]: # hsp
            next_temp = next_temperature(popt, prev_temp, 1, weather[idx]) # 1 is heat
            actions.append(1)
        elif prev_temp > epoch[1]: # csp
            next_temp = next_temperature(popt, prev_temp, 2, weather[idx]) # 2 is cool
            actions.append(2)
        else:
            next_temp = next_temperature(popt, prev_temp, 0, weather[idx]) # 0 is off
            actions.append(0)
        output.append(next_temp)
        prev_temp = next_temp

    return output, actions

def get_model_per_zone(targetday = "2018-02-01 00:00:00 PST"):
    zones = [x['?zone']['Namespace']+'#'+x['?zone']['Value'] for x in hod.do_query(zone_query % SITE, values_only=False)['Rows']]

    #targetday = "2018-02-01 00:00:00 PST"
    targetday = datetime.strptime(targetday, "%Y-%m-%d %H:%M:%S %Z")
    targetday = pytz.timezone('US/Pacific').localize(targetday)

    T0 = (targetday - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")
    T1 = (targetday - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S %Z")

    ret = {}
    for zone in zones:
        print thermostat_state_query % (SITE, zone)
        tstat_data_query = {
            "Composition": ["tstat_sensor", "tstat_state","1c467b79-b314-3c1e-83e6-ea5e7048c37b"],
            "Selectors": [MEAN, MAX, MEAN],
            "Variables": [
                {
                    "Name": "tstat_sensor",
                    "Definition": thermostat_temp_query % (SITE, zone),
                    "Units": "F",
                },
                {
                    "Name": "tstat_state",
                    "Definition": thermostat_state_query % (SITE, zone),
                },
            ],
            "Time": {
                "T0": T0, "T1": T1,
                "WindowSize": '30m',
                "Aligned": True,
            }
        }
        resp = mdal.do_query(tstat_data_query, timeout=120)
        if resp.get('error'):
            print resp['error']
            continue
        df = resp['df']
        df.columns = ['tin','a','toutside'] # inside temperature, action, outside temperature
        # column for heating
        df['a1'] = df.apply(f1, axis=1)
        # column for cooling
        df['a2'] = df.apply(f2, axis=1)
        # pad tempertures to fill holes
        df['tin'] = df['tin'].replace(to_replace=0, method='pad')
        df['toutside'] = df['toutside'].replace(to_replace=0, method='pad')
        # shift inside temperature to get the next timestamp's temperature
        df['temp_next'] = df['tin'].shift(-1)

        df=df.dropna()
        print df.describe()
        thermal_data = shuffle(df)
        popt, pcov = curve_fit(func, thermal_data[['tin','a1','a2','toutside']].T.as_matrix(), thermal_data['temp_next'].as_matrix())
        print popt
        ret[zone] = popt
    return ret

# start at midnight
test_schedule = [
    # midnight - 8:00am
    (50, 90),(50, 90), (50, 90),(50, 90), (50, 90),(50, 90), (50, 90),(50, 90), (50, 90),(50, 90), (50, 90),(50, 90), (50, 90),(50, 90), (50, 90),(50, 90), 
    # 8:00am - 4:00pm
    (70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),(70, 74),
    # 4:00pm - 6:00pm
    (70, 74),(70, 74),(70, 74),(70, 74),
    # 6:00pm - 12:00am
    (50, 90),(50, 90),(50, 90),(50, 90),(50, 90),(50, 90),(50, 90),(50, 90),(50, 90),(50, 90),(50, 90),(50, 90)
]


if __name__ == "__main__":
    models = get_model_per_zone("2018-01-11 00:00:00 PST") # don't use data after this argument
    for zone, model in models.items():
        print zone
        temperatures, actions = execute_schedule("2018-01-11 00:00:00 PST", test_schedule, model, 70) # 70 is starting temperature
        print "Temp:", temperatures
        print "HVAC:", actions
