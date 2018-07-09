from collections import defaultdict
from xbos import get_client
from util import get_start, get_tomorrow
from xbos.services import mdal
from datetime import datetime, date, timedelta
from dateutil import rrule
import json
import pytz
import config

occupancy_query = """SELECT * FROM %s WHERE {
    ?occ rdf:type/rdfs:subClassOf* brick:Occupancy_Sensor .
    ?occ bf:hasLocation ?room .
    ?room bf:isPartOf ?zone .
    ?zone rdf:type brick:HVAC_Zone .
    ?occ bf:uuid ?occ_uuid
};""" % config.SITE

occupancy_data_query = {
    "Composition": ["occ"],
    "Selectors": [mdal.MAX],
    "Variables": [
        {
            "Name": "occ",
            "Definition": occupancy_query,
        },
    ],
}

# TODO:
# - predicted occupancy for the day
# - occupancy so far (if known)
# - return per-zone occupancy
def get_occupancy(last, bucketsize):
    """
    We deliver historical occupancy up until "now". If the building has occupancy sensors, we pull that data
    and aggregate it by zone. Take mean occupancy per zone (across all sensors). 

    If building does *not* have occupancy sensors, then we need to read the results from some occupancy file.
    """
    if last not in ['hour','day','week']:
        return "Must be hour, day, week"
    start_date = get_start(last)

    zones = defaultdict(list)
    md = config.HOD.do_query(occupancy_query)
    for row in md['Rows']:
        zones[row['?zone']].append(row['?occ_uuid'])

    q = occupancy_data_query.copy()
    prediction_start = datetime.now(config.TZ)
    q["Time"] = {
        "T0": start_date.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "T1": prediction_start.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "WindowSize": bucketsize,
        "Aligned": True,
    }
    resp = config.MDAL.do_query(q, timeout=120)
    if 'error' in resp:
        print 'ERROR', resp
        return
    df = resp['df'].fillna(method='ffill')

    for zone, uuidlist in zones.items():
        if len(uuidlist) > 0:
            zones[zone] = json.loads(df[uuidlist].mean(axis=1).to_json())
        else:
            zones[zone] = {}

    # now we have data up until now; need to generate data until end of day
    prediction_end = get_tomorrow() 
    predicted = list(rrule.rrule(freq=rrule.HOURLY, dtstart=prediction_start, until=prediction_end))
    for zone, occdict in zones.items():
        for date in predicted:
            occdict[int(int(date.strftime('%s'))*1000)] = 0 # prediction
        zones[zone] = occdict
    return zones

if __name__ == '__main__':
    o = get_occupancy('day','1h')
    for zone, od in o.items():
        for t in sorted(od.keys()):
            print zone, datetime.fromtimestamp(int(t)/1000).strftime("%Y-%m-%d %H:%M:%S %Z")
