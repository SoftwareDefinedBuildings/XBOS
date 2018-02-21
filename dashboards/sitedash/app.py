from flask import Flask
from flask import abort
from flask import Response
from flask import render_template
from flask import request
from flask import jsonify
from flask_basicauth import BasicAuth
from collections import defaultdict
from itertools import groupby
from datetime import datetime, date, timedelta
import pytz
import msgpack
import os

from xbos import get_client
from xbos.services import hod, mdal

SITE = 'ciee'

def get_today():
    d = datetime.now()
    return datetime(year=d.year, month=d.month, day=d.day, tzinfo=pytz.timezone("US/Pacific"))

def prevmonday(num):
    """
    Return unix SECOND timestamp of "num" mondays ago
    """
    today = get_today()
    lastmonday = today - timedelta(days=today.weekday(), weeks=num)
    return lastmonday

hodclient = hod.HodClient("xbos/hod")
mdalclient = mdal.MDALClient("xbos/mdal")
c = get_client()

app = Flask(__name__, static_url_path='')

@app.route('/api/power/weekly/<numweeks>')
def weeklypower(numweeks):
    monday = prevmonday(int(numweeks))
    print monday
    query = {
        "Composition": ["meter"],
        "Selectors": [mdal.MEAN],
        "Variables": [
            {"Name": "meter",
             "Definition": "SELECT ?meter_uuid FROM %s WHERE { ?meter rdf:type brick:Building_Electric_Meter . ?meter bf:uuid ?meter_uuid };" % SITE,
             "Units": "kW"}
        ],
        "Time": {
            "T0": monday.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "T1": get_today().strftime("%Y-%m-%d %H:%M:%S %Z"),#(monday + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
            "WindowSize": "30m",
            "Aligned": True
        },
    }
    print query
    resp = mdalclient.do_query(query, timeout=60)
    if 'error' in resp:
        print 'ERROR', resp
        abort(500)
        abort(Response(status=resp['error']))
        return
    else:
        resp['df'].columns = ['readings']
        return resp['df'].resample('7d').apply(sum).to_json()
    return "ok"

@app.route('/api/power/monthly/<nummonths>')
def monthlypower(nummonths):
    nummonths = int(nummonths)
    if nummonths < 2:
        nummonths = 2
    today = get_today()
    firstdayofmonth = today.replace(day=1)
    query = {
        "Composition": ["meter"],
        "Selectors": [mdal.MEAN],
        "Variables": [
            {"Name": "meter",
             "Definition": "SELECT ?meter_uuid FROM %s WHERE { ?meter rdf:type brick:Building_Electric_Meter . ?meter bf:uuid ?meter_uuid };" % SITE,
             "Units": "kW"}
        ],
        "Time": {
            "T0": (firstdayofmonth - timedelta(days=30*nummonths)).strftime("%Y-%m-%d %H:%M:%S %Z"),
            "T1": firstdayofmonth.strftime("%Y-%m-%d %H:%M:%S %Z"),#(monday + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
            "WindowSize": "30m",
            "Aligned": True
        },
    }
    print query
    resp = mdalclient.do_query(query, timeout=60)
    if 'error' in resp:
        print 'ERROR', resp
        abort(500)
        abort(Response(status=resp['error']))
        return
    else:
        resp['df'].columns = ['readings']
        return resp['df'].resample('30d').apply(sum).to_json()
    return "ok"


# does SUM
@app.route('/api/power/daily/<numdays>')
def dailypower(numdays):
    query = {
        "Composition": ["meter"],
        "Selectors": [mdal.MEAN],
        "Variables": [
            {"Name": "meter",
             "Definition": "SELECT ?meter_uuid FROM %s WHERE { ?meter rdf:type brick:Building_Electric_Meter . ?meter bf:uuid ?meter_uuid };" % SITE,
             "Units": "kW"}
        ],
        "Time": {
            "T0": (get_today() - timedelta(days=int(numdays))).strftime("%Y-%m-%d %H:%M:%S %Z"),
            "T1": get_today().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "WindowSize": "30m",
            "Aligned": True
        },
    }
    print query
    resp = mdalclient.do_query(query, timeout=60)
    if 'error' in resp:
        print 'ERROR', resp
        abort(500)
        abort(Response(status=resp['error']))
        return
    else:
        resp['df'].columns = ['readings']
        return resp['df'].resample('1d').apply(sum).to_json()
    return "ok"

@app.route('/api/power/hourly/<numdays>')
def hourlypower(numdays):
    query = {
        "Composition": ["meter"],
        "Selectors": [mdal.MEAN],
        "Variables": [
            {"Name": "meter",
             "Definition": "SELECT ?meter_uuid FROM %s WHERE { ?meter rdf:type brick:Building_Electric_Meter . ?meter bf:uuid ?meter_uuid };" % SITE,
             "Units": "kW"}
        ],
        "Time": {
            "T0": (get_today() - timedelta(days=int(numdays))).strftime("%Y-%m-%d %H:%M:%S %Z"),
            "T1": get_today().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "WindowSize": "30m",
            "Aligned": True
        },
    }
    print query
    resp = mdalclient.do_query(query, timeout=60)
    if 'error' in resp:
        print 'ERROR', resp
        abort(500)
        abort(Response(status=resp['error']))
        return
    else:
        resp['df'].columns = ['readings']
        return resp['df'].resample('1h').apply(sum).to_json()
    return "ok"


@app.route('/api/power')
def streampower():
    resp = hodclient.do_query("SELECT ?meter_uri FROM %s WHERE { ?meter rdf:type brick:Building_Electric_Meter . ?meter bf:uri ?meter_uri };" % SITE)
    if resp['Count'] > 0:
        uri = resp['Rows'][0]['?meter_uri']+'/signal/meter'
        h = c.query(uri)
        if len(h) == 0:
            abort(500)
            abort(Response(status='NO RESPONSE from ' + uri))
            return
        if len(h[0].payload_objects) == 0:
            abort(500)
            abort(Response(status='NO data from ' + uri))
            return
        status = msgpack.unpackb(h[0].payload_objects[0].content)
        if status is None:
            abort(500)
            abort(Response(status='Could not decode data from' + uri))
            return
        return jsonify({'demand': status['current_demand']})
    return 'NO METER'

def read_uri(uri):
    h = c.query(uri)
    if len(h) == 0:
        return {}
    if len(h[0].payload_objects) == 0:
        return {}
    status = msgpack.unpackb(h[0].payload_objects[0].content)
    if status is None:
        return {}
    return status

#def read_uri_sub(uri):
#    h = c.subscribe(uri, cb)
#    if len(h) == 0:
#        return {}
#    if len(h[0].payload_objects) == 0:
#        return {}
#    status = msgpack.unpackb(h[0].payload_objects[0].content)
#    if status is None:
#        return {}
#    return status

@app.route('/api/hvac')
def hvacstate():
    resp = hodclient.do_query("""
SELECT * FROM %s WHERE {
  ?rtu rdf:type brick:RTU .
  ?rtu bf:feeds ?zone .
  ?zone rdf:type brick:HVAC_Zone .
  ?rtu bf:isControlledBy ?tstat .
  ?zone bf:hasPart ?room .
  ?room bf:hasPoint ?sensor .
  ?sensor rdf:type/rdfs:subClassOf* brick:Temperature_Sensor .
  ?tstat bf:uri ?tstat_uri .
  ?sensor bf:uri ?sensor_uri
 };""" % SITE)
    print resp
    zones = defaultdict(lambda : defaultdict(dict))
    if resp['Count'] == 0:
        return 'NO RESULTS'
    for row in resp['Rows']:
        zonename = row['?zone']
        roomname = row['?room']
        tstat = read_uri(row['?tstat_uri']+'/signal/info')
        zones[zonename]['heating_setpoint'] = tstat['heating_setpoint']
        zones[zonename]['cooling_setpoint'] = tstat['cooling_setpoint']
        zones[zonename]['tstat_temperature'] = tstat['temperature']
        zones[zonename]['heating'] = tstat['state'] == 1
        zones[zonename]['cooling'] = tstat['state'] == 2
        zones[zonename]['timestamp'] = int(tstat['time']/1e9)
        zones[zonename]['rooms'][roomname] = {'sensors': []}

    for row in resp['Rows']:
        zonename = row['?zone']
        roomname = row['?room']
        uri = row['?sensor_uri']
        data = read_uri(uri)
        if len(data) > 0:
            s = {
                'uri': uri,
                'temperature': data['temperature'],
                'relative_humidity': data['relative_humidity']
            }
            zones[zonename]['rooms'][roomname]['sensors'].append(s)

    return jsonify(zones)
