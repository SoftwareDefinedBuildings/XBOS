from collections import defaultdict
from xbos import get_client
from util import get_start, get_tomorrow
from xbos.services import mdal
from datetime import datetime, date, timedelta
from dateutil import rrule
import pandas as pd
import sqlite3
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

zone_query = """SELECT * FROM %s WHERE {
    ?zone rdf:type brick:HVAC_Zone .
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
    prediction_start = datetime.now(config.TZ)

    md = config.HOD.do_query(occupancy_query)
    if md['Rows'] is not None:
        for row in md['Rows']:
            zones[row['?zone']].append(row['?occ_uuid'])
        q = occupancy_data_query.copy()
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

        # get predicted output
        prediction_end = get_tomorrow() 
        predicted = list(rrule.rrule(freq=rrule.HOURLY, dtstart=prediction_start, until=prediction_end))
        for zone, occdict in zones.items():
            for date in predicted:
                occdict[int(int(date.strftime('%s'))*1000)] = 'predicted' # prediction
            zones[zone] = occdict
    else:
        md = config.HOD.do_query(zone_query)
        zonenames = [x['?zone'].lower() for x in md['Rows']]
        conn = sqlite3.connect('occupancy_schedule.db')
        sql = conn.cursor()
        for zone in zonenames:
            query = "SELECT * FROM schedules WHERE site='{0}' and zone='{1}' and dayofweek='{2}'".format(config.SITE, zone, prediction_start.strftime('%A').lower())
            res = sql.execute(query).fetchall()
            records = {'time': [], 'occ': [], 'zone': []}
            for sqlrow in res:
                hour, minute = sqlrow[3].split(':')
                time = datetime(year=prediction_start.year, month=prediction_start.month, day=prediction_start.day, hour=int(hour), minute=int(minute), tzinfo=prediction_start.tzinfo)
                occ = sqlrow[5]
                zone = sqlrow[1]
                records['time'].append(time)
                records['occ'].append(occ)
                records['zone'].append(zone)
            df = pd.DataFrame.from_records(records)
            df = df.set_index(df.pop('time'))
            if len(df) ==0:
                continue
            sched = df.resample(bucketsize.replace('m','T')).ffill()
            zones[zone] = json.loads(sched['occ'].to_json())
        conn.close()

    return zones

if __name__ == '__main__':
    o = get_occupancy('day','1h')
    for zone, od in o.items():
        for t in sorted(od.keys()):
            print zone, datetime.fromtimestamp(int(t)/1000).strftime("%Y-%m-%d %H:%M:%S %Z"), od[t]
