# XBOS Python 

This is an aggregate package to bring together all XBOS clients under a single package

Current version: 0.0.27


## Usage

Working with a thermostat
```python
from xbos import get_client
from xbos.devices.thermostat import Thermostat

# get a bosswave client
c = get_client() # defaults to $BW2_AGENT, $BW2_DEFAULT_ENTITY

# instantiate a thermostat
tstat = Thermostat(c, "410testbed/devices/venstar/s.venstar/420lab/i.xbos.thermostat")

# print cached state; blocks until we get first report.
# maintains subscription in background.
print tstat.heating_setpoint

# batch actuation
state = {
    "heating_setpoint": 72,
    "cooling_setpoint": 76
}
tstat.write(state)

# or individually
tstat.set_heating_setpoint(72)
```

Interacting with an archiver

```python
from xbos import get_client
from xbos.services.pundat import DataClient, timestamp, make_dataframe

# get a bosswave client
c = get_client() # defaults to $BW2_AGENT, $BW2_DEFAULT_ENTITY

dc = DataClient(c,archivers=["ucberkeley"])

uuids = dc.uuids('name = "air_temp" and Deployment = "CIEE"')

# get timestamps
start = timestamp('6/25/2017')
end = timestamp('6/28/2017')

# get 1-hour window data for the first uuid
data = dc.window_uuids(uuids[0], start, end, '1h')

# get a dataframe from the results, keyed by the UUID
dfs = make_dataframe(data)
print dfs[uuids[0]].describe()
```

Interacting with HodDB

```python
from xbos.services.hod import HodClientHTTP

hc = HodClientHTTP("http://ciee.cal-sdb.org")

q = """
SELECT ?x ?uri WHERE {
    ?x rdf:type/rdfs:subClassOf* brick:Temperature_Sensor .
    ?x bf:uri ?uri .
};
"""
print hc.do_query(q)
#[{u'?uri': u'ciee/sensors/s.hamilton/00126d0700000060/i.temperature/signal/operative',
#    u'?x': u'hamilton_0060_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000005e/i.temperature/signal/operative',
#    u'?x': u'hamilton_005e_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000005d/i.temperature/signal/operative',
#    u'?x': u'hamilton_005d_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000005c/i.temperature/signal/operative',
#    u'?x': u'hamilton_005c_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000005b/i.temperature/signal/operative',
#    u'?x': u'hamilton_005b_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000005a/i.temperature/signal/operative',
#    u'?x': u'hamilton_005a_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000002e/i.temperature/signal/operative',
#    u'?x': u'hamilton_002e_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000002c/i.temperature/signal/operative',
#    u'?x': u'hamilton_002c_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000002b/i.temperature/signal/operative',
#    u'?x': u'hamilton_002b_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d070000002a/i.temperature/signal/operative',
#    u'?x': u'hamilton_002a_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d0700000029/i.temperature/signal/operative',
#    u'?x': u'hamilton_0029_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d0700000028/i.temperature/signal/operative',
#    u'?x': u'hamilton_0028_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d0700000027/i.temperature/signal/operative',
#    u'?x': u'hamilton_0027_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d0700000025/i.temperature/signal/operative',
#    u'?x': u'hamilton_0025_air_temp'},
#{u'?uri': u'ciee/sensors/s.hamilton/00126d0700000022/i.temperature/signal/operative',
#    u'?x': u'hamilton_0022_air_temp'}]
```

Putting it all together

```python
from xbos import get_client
from xbos.services.pundat import DataClient, timestamp, make_dataframe
from xbos.services.hod import HodClientHTTP
from xbos.devices.thermostat import Thermostat

# get a bosswave client
c = get_client() # defaults to $BW2_AGENT, $BW2_DEFAULT_ENTITY
# get a HodDB client
hc = HodClientHTTP("http://ciee.cal-sdb.org")

# query for CIEE thermostats
q = """
SELECT ?tstat ?uri WHERE {
    ?tstat rdf:type brick:Thermostat .
    ?tstat bf:uri ?uri .
};
"""
ciee_tstats = hc.do_query(q)

# instantiate some classes
tstats = {}
for info in ciee_tstats:
    tstats[info['?tstat']] = Thermostat(c, info['?uri'])

# print some settings
for name, tstat in tstats.items():
    print name, 'has heat/cool', tstat.heating_setpoint, tstat.cooling_setpoint
```


## Layout:
- `xbos`:
    - `__init__.py`
    - `devices`:
        - `__init__.py`
        - `thermostat.py`
        - `plug.py`
        - etc...
    - `services`:
        - `__init__.py`
        - `pundat.py`
        - `hoddb.py`
        - `mdal.py`
