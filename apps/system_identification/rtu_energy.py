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

# store zone name to thermostat
zone2tstat = {}
# store zone name to meter for the RTU for that zone
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



def get_thermostat_meter_data(zone):
    """
    This method subscribes to the output of the meter for the given zone.
    It returns a handler to call when you want to stop subscribing data, which
    returns a list of the data readins over that time period
    """
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
    """
    Adjusts the temperature setpoints in order to call for heating. Returns
    a handler to call when you want to reset the thermostat
    """
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

def call_cool(tstat):
    """
    Adjusts the temperature setpoints in order to call for cooling. Returns
    a handler to call when you want to reset the thermostat
    """
    current_hsp, current_csp = tstat.heating_setpoint, tstat.cooling_setpoint
    current_temp = tstat.temperature
    tstat.write({
        'heating_setpoint': current_temp-20,
        'cooling_setpoint': current_temp-10,
        'mode': COOL,
    })

    def restore():
        tstat.write({
            'heating_setpoint': current_hsp,
            'cooling_setpoint': current_csp,
            'mode': AUTO,
        })
    return restore

def call_fan(tstat):
    """
    Toggles the fan
    """
    old_fan = tstat.fan

    tstat.write({
        'fan': not old_fan,
    })

    def restore():
        tstat.write({
            'fan': old_fan,
        })
    return restore


def run_experiment(my_tstat, func, label):
    print "Start subscribing to meter data"
    getdata = get_thermostat_meter_data(zone)

    time.sleep(10)
    print "Thermostat calling for {}".format(label)
    restore = func(my_tstat)
    print "{} for 10 min".format(label)
    time.sleep(600)
    print "Restoring previous state (wait another 10 min)"
    restore()
    time.sleep(600)

    print "Getting data from meter"
    data = getdata()
    print "Data: {}".format(data)
    d = pd.Series(data)
    print 'Power diff for on {}'.format(d.diff().max())
    print 'Power diff for off {}'.format(-d.diff().min())


# iterate through each zone. We want to "disable" the other thermostats
# on each iteration so they don't affect our measurements, so we set the
# other thermostat modes to OFF.
for zone in zone2tstat.keys():
    print "Running tests for zone {}".format(zone)
    my_tstat = zone2tstat[zone]
    other_tstats = [tstat for otherzone, tstat in zone2tstat.items() if otherzone != zone]

    print "Disabling other thermostats"
    for tstat in other_tstats:
        tstat.set_mode(OFF)
    time.sleep(30)


    print " ### HEATING"
    run_experiment(my_tstat, call_heat, "heat")
    print  'Wait for 10 min'
    time.sleep(600)

    print " ### COOLING"
    run_experiment(my_tstat, call_cool, "cool")
    print 'Wait for 10 min'
    time.sleep(600)

    print " ### FAN"
    run_experiment(my_tstat, call_fan, "fan")
    print 'Wait for 10 min'
    time.sleep(600)

    print 'Resetting thermostats'
    for tstat in other_tstats:
        tstat.set_mode(AUTO)
    print 'Wait for 10 min, then go to next zone'
    time.sleep(600)

