import pymortar
import pandas as pd
import pendulum
import toml
from flask import Flask
from flask import jsonify, send_from_directory
from flask import request
from flask import current_app
from flask import make_response
from flask import render_template
from collections import defaultdict
from functools import update_wrapper
import pytz
import json
from datetime import datetime, timedelta
from dashutil import get_start, generate_months, prevmonday, get_today
from datetime import timezone
import xsg

config = toml.load('config.toml')

TZ = pytz.timezone('US/Pacific')

app = Flask(__name__, static_url_path='/static')

client = pymortar.Client({
	'mortar_address':config['Mortar']['url'], 
	'username': config['Mortar']['username'],
	'password': config['Mortar']['password'],
})
sites = [config['Dashboard']['sitename']]

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

def state_to_string(state):
    if state == 0:
        return 'off'
    elif state == 1:
        return 'heat stage 1'
    elif state == 2:
        return 'cool stage 1'
    elif state == 4:
        return 'heat stage 2'
    elif state == 5:
        return 'cool stage 2'
    else:
        return 'unknown'

def dofetch(views, dataframes, start=None, end=None):
    timeparams = None
    if start is not None and end is not None:
        timeparams=pymortar.TimeParams(
            start=start.isoformat(),
            end=end.isoformat(),
        )
    req = pymortar.FetchRequest(
        sites=sites,
        views=views,
        dataFrames=dataframes,
        time=timeparams
    )

    return client.fetch(req)

meter_view = pymortar.View(
        name="meters",
        definition="""SELECT ?meter WHERE {
            ?meter rdf:type brick:Building_Electric_Meter
        };""",
    )
meter_df = pymortar.DataFrame(
        name="meters",
        aggregation=pymortar.MEAN,
        timeseries=[
            pymortar.Timeseries(
                view="meters",
                dataVars=['?meter'],
            )
        ]
    )

tstats_view = pymortar.View(
    name="tstats",
    definition="""SELECT ?rtu ?zone ?tstat ?csp ?hsp ?temp ?state WHERE {
      ?rtu rdf:type brick:RTU .
      ?tstat bf:controls ?rtu .
      ?rtu bf:feeds ?zone .
      ?tstat bf:hasPoint ?temp .
      ?temp rdf:type/rdfs:subClassOf* brick:Temperature_Sensor .

      ?tstat bf:hasPoint ?csp .
      ?csp rdf:type/rdfs:subClassOf* brick:Supply_Air_Temperature_Heating_Setpoint .

      ?tstat bf:hasPoint ?hsp .
      ?hsp rdf:type/rdfs:subClassOf* brick:Supply_Air_Temperature_Cooling_Setpoint .

      ?tstat bf:hasPoint ?state .
      ?state rdf:type brick:Thermostat_Status .
    };""",
)

tstats_df = pymortar.DataFrame(
    name="tstats",
    aggregation=pymortar.MAX,
    timeseries=[
        pymortar.Timeseries(
            view="tstats",
            dataVars=['?csp','?hsp','?temp','?state'],
        ),
    ]
)

room_temp_view = pymortar.View(
    name="room_temp",
    definition="""SELECT ?zone ?room ?sensor WHERE {
        ?zone rdf:type brick:HVAC_Zone .
        ?zone bf:hasPart ?room .
        ?sensor rdf:type/rdfs:subClassOf* brick:Temperature_Sensor .
        ?room bf:hasPoint ?sensor  .
    };""",
)

weather_view = pymortar.View(
    name="weather_temp",
    definition="""SELECT ?sensor WHERE {
    ?sensor rdf:type/rdfs:subClassOf* brick:Weather_Temperature_Sensor .
    };""",
)

weather_df = pymortar.DataFrame(
    name="weather_temp",
    aggregation=pymortar.MEAN,
    window='15m',
    timeseries=[
        pymortar.Timeseries(
            view="weather_temp",
            dataVars=['?sensor'],
        )
    ],
)

@app.route('/api/power/<last>/in/<bucketsize>')
@crossdomain(origin='*')
def power_summary(last, bucketsize):
    # first, determine the start date from the 'last' argument
    start_date = get_start(last)
    if last == 'year' and bucketsize == 'month':
        ranges = generate_months(get_today().month - 1)
        readings = []
        times = []
        for t0,t1 in ranges:
            meter_df.window = '{0}d'.format((t0-t1).days)
            res=dofetch([meter_view], [meter_df], t1, t0)
            times.append(t1.tz_convert(TZ).timestamp()*1000)
            readings.append(res['meters'].fillna('myNullVal').values[0][0])
        return jsonify({'readings': dict(zip(times,readings))})

    # otherwise,
    meter_df.window=bucketsize
    print('start_date',start_date)
    res=dofetch([meter_view], [meter_df], start_date, datetime.now(TZ))
    res['meters'].columns=['readings']
    return res['meters'].tz_convert(TZ).fillna('myNullVal').to_json()

@app.route('/api/energy/<last>/in/<bucketsize>')
@crossdomain(origin='*')
def energy_summary(last, bucketsize):
    start_date = get_start(last)
    if last == 'year' and bucketsize == 'month':
        ranges = generate_months(get_today().month - 1)
        readings = []
        times = []
        for t0,t1 in ranges:
            meter_df.window = '15m'
            res=dofetch([meter_view], [meter_df], t1, t0)
            df = res['meters'].copy()
            df.columns = ['readings']
            df /= 4. # divide by 4 to get 15min (kW) -> kWh
            times.append(pd.to_datetime(t1.isoformat()))
            readings.append(df['readings'].sum())
        df = pd.DataFrame(readings,index=times,columns=['readings'])
        return df.fillna('myNullVal').to_json()

    meter_df.window = '15m'
    print('start_date',start_date)
    res = dofetch([meter_view], [meter_df], start_date, datetime.now(TZ))
    df = res['meters'].tz_convert(TZ).copy()
    df.columns = ['readings']
    df['readings'] /= 4.
    return df.fillna('myNullVal').resample(bucketsize).apply(sum).to_json()

@app.route('/api/price')
@crossdomain(origin='*')
def price():
    res = xsg.get_price(sites[0], get_today(), get_today()+timedelta(days=1))
    return res['price'].to_json()

@app.route('/api/power')
@crossdomain(origin='*')
def current_power():
    raise(Exception("/api/power NOT IMPLEMENTED"))
    pass

@app.route('/api/hvac')
@crossdomain(origin='*')
def hvacstate():
    t1 = datetime.now(TZ).replace(microsecond=0)
    t0 = t1 - timedelta(hours=12)
    tstats_df.window='1h'
    res = dofetch([tstats_view, room_temp_view], [tstats_df], t0, t1)
    zones = defaultdict(lambda : defaultdict(dict))
    for (tstat, zone, hsp, csp, temp, state) in res.query('select tstat, zone, hsp_uuid, csp_uuid, temp_uuid, state_uuid from tstats'):
        zone = zone.split('#')[-1]
        tempdf = res['tstats'][[hsp,csp,temp,state]].tail(1).fillna('myNullVal')
        hsp,csp,temp,state = tempdf.values[-1]
        zones[zone]['heating_setpoint'] = hsp
        zones[zone]['cooling_setpoint'] = csp
        zones[zone]['tstat_temperature'] = temp
        zones[zone]['heating'] = bool(state == 1  or state == 4)
        zones[zone]['cooling'] = bool(state == 2 or state == 5)
        zones[zone]['timestamp'] = tempdf.index[-1].timestamp() * 1000

    return jsonify(zones)

@app.route('/api/hvac/day/in/<bucketsize>')
@crossdomain(origin='*')
def serve_historipcal_hvac(bucketsize):
    t1 = datetime.now(TZ).replace(microsecond=0)
    t0 = get_today()
    tstats_df.window=bucketsize
    res = dofetch([tstats_view, weather_view], [tstats_df, weather_df], t0, t1)
    zones = defaultdict(lambda : defaultdict(dict))
    df = res['tstats'].fillna(method='ffill').fillna(method='bfill')
    for (tstat, zone, hsp, csp, temp, state) in res.query('select tstat, zone, hsp_uuid, csp_uuid, temp_uuid, state_uuid from tstats'):
        zone = zone.split('#')[-1]
        zones[zone]['inside'] = json.loads(df[temp].dropna().to_json())
        zones[zone]['heating'] = json.loads(df[hsp].dropna().to_json())
        zones[zone]['outside'] = json.loads(res['weather_temp'].max(axis=1).dropna().to_json())
        zones[zone]['cooling'] = json.loads(df[csp].dropna().to_json())
        zones[zone]['state'] = json.loads(df[state].dropna().apply(state_to_string).to_json())
        for k, values in zones[zone].items():
            if len(values) == 0:
                fakedates = pd.date_range(t0, t1, freq=bucketsize.replace('m','T'))
                if k != 'state':
                    fakevals = [0]*len(fakedates)
                else:
                    fakevals = ['off']*len(fakedates)
                zones[zone][k] = json.loads(pd.DataFrame(fakevals,index=fakedates)[0].to_json())
    return jsonify(zones)

@app.route('/api/hvac/day/<bucketsize>')
@crossdomain(origin='*')
def get_temp_per_zone(bucketsize):
    t1 = datetime.now(TZ).replace(microsecond=0)
    t0 = get_today()
    tstats_df.window=bucketsize
    res = dofetch([tstats_view, weather_view], [tstats_df, weather_df], t0, t1)
    zones = defaultdict(lambda : defaultdict(dict))
    df = res['tstats']
    for (zone, temp) in res.query('select zone, temp_uuid from tstats'):
        zone = zone.split('#')[-1]
        zones[zone] = json.loads(df[temp].fillna('myNullVal').to_json())
    return jsonify(zones)

@app.route('/api/prediction/hvac/day/in/<bucketsize>')
@crossdomain(origin='*')
def serve_prediction_hvac(bucketsize):
    pass

@app.route('/api/prediction/dr')
@crossdomain(origin='*')
def serve_prediction_dr():
    return jsonify({'days': [{'date': 1558126800, 'likelihood': 'likely'}]})

def format_simulation_output(output):
    # actions -> number to label
    for zone, data in output.items():
        data['state'] = {int(t/1e6): state_to_string(v) for t,v in data.pop('actions').items()}
        data['inside'] = {int(t/1e6): v for t,v in data.pop('temperatures').items()}
        data['outside'] = {t: 30 for t in data['inside'].keys()}
        data['cooling'] = {t: 30 for t in data['inside'].keys()}
        data['heating'] = {t: 30 for t in data['inside'].keys()}
        output[zone] = data
    return output

@app.route('/api/simulation/<drlambda>/<date>')
def simulate_lambda_site(drlambda, date):
    ret = {}
    for zone in xsg.get_zones(sites[0]):
        start = pendulum.parse(date, tz='US/Pacific')
        # TODO: change back to 12
        end = start.add(hours=1)
        fmt = '%Y-%m-%dT%H:%M:%S%z'
        start = datetime.strptime(start.strftime(fmt), fmt)
        end = datetime.strptime(end.strftime(fmt), fmt)

        try:
            res = xsg.simulation(sites[0], start, end, '1h', float(drlambda), zone=zone)
            # dataframe to dict
            formatted = {k: df.set_index(df.index.astype(int)).to_dict() for k, df in res.items()}
            ret.update(formatted)
            print(formatted)
            #return jsonify(formatted)
        except Exception as e:
            return jsonify({'error': 'could not get prediction', 'msg': str(e)})
    print(ret)
    return jsonify(format_simulation_output(ret))

@app.route('/api/simulation/<drlambda>/<date>/<zone>')
@crossdomain(origin='*')
def simulate_lambda(drlambda, date, zone):
    """
    TODO: do we assume that the lambda is for the peak period only: 4-7pm
        how do we do this on the backend?
    assume date is in YYYY-MM-DD
    """
    print(xsg.get_zones(sites[0]))

    start = pendulum.parse(date, tz='US/Pacific')
    end = start.add(hours=24)
    fmt = '%Y-%m-%dT%H:%M:%S%z'
    start = datetime.strptime(start.strftime(fmt), fmt)
    end = datetime.strptime(end.strftime(fmt), fmt)

    try:
        res = xsg.simulation(sites[0], start, end, '1h', float(drlambda), zone=zone)
        # dataframe to dict
        d = {k: df.set_index(df.index.astype(int)).to_dict() for k, df in res.items()}
        return jsonify(format_simulation_output(d))
    except Exception as e:
        return jsonify({'error': 'could not get prediction', 'msg': str(e)})

@app.route('/api/occupancy/<last>/in/<bucketsize>')
@crossdomain(origin='*')
def serve_occupancy(last, bucketsize):
    pass

#@app.route('/api/hvac/day/setpoints')
#@crossdomain(origin='*')
#def setpoint_today():
#    pass

@app.route('/<filename>')
@crossdomain(origin='*')
def home(filename):
    return send_from_directory('templates', filename)
    #return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
