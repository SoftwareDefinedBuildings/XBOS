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

SITE = 'avenal-public-works-yard'

def prevmonday(num):
    """
    Return unix SECOND timestamp of "num" mondays ago
    """
    today = date.today()
    lastmonday = today - timedelta(days=today.weekday(), weeks=num)
    return lastmonday

hodclient = hod.HodClient("xbos/hod")
mdalclient = mdal.BOSSWAVEMDALClient("xbos/mdal")
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
             "Definition": "SELECT ?meter_uuid FROM %s WHERE { ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter . ?meter bf:uuid ?meter_uuid };" % SITE,
             "Units": "kW"}
        ],
        "Time": {
            "T0": monday.strftime("%Y-%m-%d %H:%M:%S"),
            "T1": date.today().strftime("%Y-%m-%d %H:%M:%S"),#(monday + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
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
    today = date.today()
    firstdayofmonth = today.replace(day=1)
    query = {
        "Composition": ["meter"],
        "Selectors": [mdal.MEAN],
        "Variables": [
            {"Name": "meter",
             "Definition": "SELECT ?meter_uuid FROM %s WHERE { ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter . ?meter bf:uuid ?meter_uuid };" % SITE,
             "Units": "kW"}
        ],
        "Time": {
            "T0": (firstdayofmonth - timedelta(days=30*nummonths)).strftime("%Y-%m-%d %H:%M:%S"),
            "T1": firstdayofmonth.strftime("%Y-%m-%d %H:%M:%S"),#(monday + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S"),
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
             "Definition": "SELECT ?meter_uuid FROM %s WHERE { ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter . ?meter bf:uuid ?meter_uuid };" % SITE,
             "Units": "kW"}
        ],
        "Time": {
            "T0": (date.today() - timedelta(days=int(numdays))).strftime("%Y-%m-%d %H:%M:%S"),
            "T1": date.today().strftime("%Y-%m-%d %H:%M:%S"),
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

@app.route('/api/power')
def streampower():
    resp = hodclient.do_query("SELECT ?meter_uri FROM %s WHERE { ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter . ?meter bf:uri ?meter_uri };" % SITE)
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
