from xbos import get_client
# for interacting with archiver
from xbos.services.pundat import DataClient, timestamp, make_dataframe, merge_dfs
# for performing Brick queries
from xbos.services.hod import HodClient
# for interacting with the thermostat control state
from xbos.devices.thermostat import Thermostat

# for deserializing messages
import msgpack
import time
import pandas as pd

# get a bosswave client
c = get_client() # defaults to $BW2_AGENT, $BW2_DEFAULT_ENTITY

# get a HodDB client
hod = HodClient("ciee/hod", c)
# get an archiver client
archiver = DataClient(c,archivers=["ucberkeley"])

# mode
OFF = 0
HEAT = 1
COOL = 2
AUTO = 3

zone2tstat = {}
zone2meter = {}
# query for the the thermostat APIs. Once we have the BOSSWAVE URI, we can instantiate
# a Thermostat object in order to control it.
query = """
SELECT ?thermostat ?zone ?uri ?meter_uri WHERE {
    ?thermostat rdf:type/rdfs:subClassOf* brick:Thermostat .
    ?zone rdf:type brick:HVAC_Zone .
    ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter .

    ?thermostat bf:controls/bf:feeds+ ?zone .
    ?thermostat bf:uri ?uri .
    ?thermostat bf:controls/bf:hasPoint ?meter .
    ?meter bf:uri ?meter_uri .
};"""
for row in hod.do_query(query)["Rows"]:
    zone = row["?zone"]
    uri = row["?uri"]
    zone2tstat[zone] = Thermostat(c, uri)
    zone2meter[zone] = row["?meter_uri"]


# iterate through each zone. We want to "disable" the other thermostats
# on each iteration so they don't affect our measurements, so we set the
# other thermostat modes to OFF.

def get_thermostat_meter_data(zone):
    meter_uri = zone2meter.get(zone, "None")
    data = []
    def cb(msg):
        for po in msg.payload_objects:
            if po.type_dotted == (2,0,9,1):
                m = msgpack.unpackb(po.content)
                data.append(m['current_demand'])
    handle = c.subscribe(meter_uri+"/signal/meter", cb)

    def stop():
        c.unsubscribe(handle)
        return data
    return stop

def call_heat(tstat):
    current_hsp, current_csp = tstat.heating_setpoint, tstat.cooling_setpoint
    current_temp = tstat.temperature
    tstat.write({
        'heating_setpoint': current_temp+10,
        'cooling_setpoint': current_temp+20,
        'mode': HEAT,
    })

    def restore():
        tstat.write({
            'heating_setpoint': current_hsp,
            'cooling_setpoint': current_csp,
            'mode': AUTO,
        })
    return restore

for zone in zone2tstat.keys():
    print zone
    print 'running!'
    my_tstat = zone2tstat[zone]
    other_tstats = [tstat for otherzone, tstat in zone2tstat.items() if otherzone != zone]
    print 'start meter sub'
    getdata = get_thermostat_meter_data(zone)

    # disable other tstats
    print 'now running'
    for tstat in other_tstats:
        tstat.set_mode(OFF)

    time.sleep(30)
    print 'set thermostat heat'
    restore = call_heat(my_tstat)
    print 'wait 3 min'
    time.sleep(180)
    print 'restoring (3 min)'
    restore()
    time.sleep(180)
    print 'get data'
    data = getdata()
    print data
    d = pd.Series(data)
    print 'on', d.diff().max()
    print 'off', -d.diff().min()
    print 'reset other tstats'
    for tstat in other_tstats:
        tstat.set_mode(AUTO)
    time.sleep(300)

