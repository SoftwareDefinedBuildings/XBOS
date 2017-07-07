# XBOS Python 

This is an aggregate package to bring together all XBOS clients under a single package


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
t
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
