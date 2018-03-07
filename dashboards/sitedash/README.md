# XBOS Site-specific Dashboard

## Running

Use Python2

```
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
FLASK_APP=app.py flask run
```

You either need a BOSSWAVE agent running on your machine, or you can run a ragent process.

## API Doc

### Power Endpoints

All of these are for full building power


### HVAC Endpoints

- `/api/power/<last>/in/<bucketsize>`
    - Parameter:
        - `last`: one of `year`,`month`,`week`,`day`,`hour`
        - `bucketsize`: follows format `{number}{unit}`
            - `number`: 1,2, etc
            - `unit`: `m` (minute), `h` (hour), `d` (day)
        - examples:
            - `30d` (30 days)
            - `1h` (1 hour)
    - Returns: JSON dictionary with key `readings`. Contains dictionary of timestamp (in milliseconds since Unix epoch) to value (in average kW over the bucket period)
        ```json
        {
            "readings": {
                "1520283178000": 4.9341614907,
                "1520286778000": 4.8949074074,
                "1520290378000": 5.3709010989,
                "1520293978000": 5.4280777538,
                "1520297578000": 4.5849350649,
                "1520301178000": 4.0717062635,
                "1520304778000": 3.8077922078,
                "1520308378000": 2.7346466809,
                "1520311978000": 2.6214782609,
                "1520315578000": 4.3803870968,
                "1520319178000": 2.9621276596,
                "1520322778000": 3.2788596491,
                "1520326378000": 2.6144347826,
                "1520329978000": 2.6460526316,
                "1520333578000": 2.6058008658,
                "1520337178000": 2.6996551724,
                "1520340778000": 2.6671583514,
                "1520344378000": 2.5568443497,
                "1520347978000": 2.8063519313,
                "1520351578000": 3.7303282276,
                "1520355178000": 4.9506753813,
                "1520358778000": 5.4251724138,
                "1520362378000": 5.8769090909,
                "1520365978000": 5.2881758242
            }
        }
        ```

- `/api/energy/<last>/in/<bucketsize>`
    - Parameter:
        - `last`: one of `year`,`month`,`week`,`day`,`hour`
        - `bucketsize`: follows format `{number}{unit}`
            - `number`: 1,2, etc
            - `unit`: `m` (minute), `h` (hour), `d` (day)
        - examples:
            - `30d` (30 days)
            - `1h` (1 hour)
    - Returns: JSON dictionary with key `readings`. Contains dictionary of timestamp (in milliseconds since Unix epoch) to value (in kWh consumed over the bucket period)
        ```json
        {
            "readings": {
                "1520283600000": 3.7010233683,
                "1520287200000": 4.950538027,
                "1520290800000": 5.3817511502,
                "1520294400000": 5.3701927621,
                "1520298000000": 4.4612059229,
                "1520301600000": 4.1477825135,
                "1520305200000": 3.394366325,
                "1520308800000": 2.5441935699,
                "1520312400000": 2.9506116217,
                "1520316000000": 4.3161760893,
                "1520319600000": 3.2669755329,
                "1520323200000": 2.7021675992,
                "1520326800000": 2.6280373823,
                "1520330400000": 2.7223003685,
                "1520334000000": 2.6381419351,
                "1520337600000": 2.6213040172,
                "1520341200000": 2.6464812995,
                "1520344800000": 2.5687484207,
                "1520348400000": 3.0593897456,
                "1520352000000": 4.1861969744,
                "1520355600000": 4.808665212,
                "1520359200000": 5.7297887332,
                "1520362800000": 5.6854134303,
                "1520366400000": 5.1711923866,
                "1520370000000": 3.7459377798
            }
        }
        ```

- `/api/hvac`:
    - get current HVAC state
    - returns:
        ```json
        {
            "zones": {
                "south zone": {
                    "timestamp": 1515443111,
                    "heating_setpoint": 66.0,
                    "cooling_setpoint": 72.0,
                    "tstat_temperature": 70.0,
                    "heating": false,
                    "cooling": false,
                    "rooms": {          # with sensors
                        "R111": {
                            "sensors": [
                                {"uri": "ciee/sensor/123", "temperature": 70.2, "humidity": 46.2},
                                {"uri": "ciee/sensor/124", "temperature": 70.2, "humidity": 46.2},
                            ]
                        },
                        "R112": {
                            "sensors": [
                                {"uri": "ciee/sensor/125", "temperature": 70.2, "humidity": 46.2},
                            ]
                        },
                        "R113": {},
                    }
                },
                "north zone": {
                    "timestamp": 1515443111,
                    "heating_setpoint": 68.0,
                    "cooling_setpoint": 74.0,
                    "tstat_temperature": 70.0,
                    "heating": true,
                    "cooling": false,
                    "rooms": {      # no sensors
                        "R212": {},
                        "R213": {}
                    }
                },
            }
        }
        ```

- `/api/hvac/day/<bucketsize>`
    - get current day of temperature data for each zone in `<bucketsize>`. Aggregates using mean
    - `bucketsize`: follows format `{number}{unit}`
        - `number`: 1,2, etc
        - `unit`: `m` (minute), `h` (hour)
    - examples:
        - `1h` (1 hour)
        - `15min` (1 minute)
    - returns: dictionary whose keys are zone names. Values are dictionaries from timestamp to temperature in Fahrenheit. Timestamps are in milliseconds since the Unix epoch
        ```json
        {
            "EastZone": {
                "1520322778000": 69.4473087819,
                "1520326378000": 69.204815864,
                "1520329978000": 69.2362606232,
                "1520333578000": 69.2615819209,
                "1520337178000": 69.2750708215,
                "1520340778000": 69.2776203966,
                "1520344378000": 69.2759206799,
                "1520347978000": 69.5719546742,
                "1520351578000": 69.2436260623,
                "1520355178000": 69.6504249292,
                "1520358778000": 70.0016997167,
                "1520362378000": 70.3898550725,
                "1520365978000": 70.4116147309,
                "1520369578000": 70.6051136364,
                "1520373178000": 70.728125,
                "1520376778000": 70.856980057,
                "1520380378000": 71.547592068,
                "1520383978000": 72.1147727273
            },
            "NorthZone": {
                "1520322778000": 75.0916905444,
                "1520326378000": 75.1257142857,
                "1520329978000": 75.1232091691,
                "1520333578000": 75.0769230769,
                "1520337178000": 75.005730659,
                "1520340778000": 75.0942857143,
                "1520344378000": 75.1171428571,
                "1520347978000": 75.18,
                "1520351578000": 75.1685714286,
                "1520355178000": 75.1685714286,
                "1520358778000": 75.0143266476,
                "1520362378000": 75.0,
                "1520365978000": 75.0,
                "1520369578000": 75.0,
                "1520373178000": 75.3180515759,
                "1520376778000": 76.0,
                "1520380378000": 76.0,
                "1520383978000": 76.0
            },
            "SouthZone": {
                "1520322778000": 73.0,
                "1520326378000": 73.0,
                "1520329978000": 73.0,
                "1520333578000": 73.0,
                "1520337178000": 73.0,
                "1520340778000": 73.0,
                "1520344378000": 73.0,
                "1520347978000": 73.0,
                "1520351578000": 73.0,
                "1520355178000": 73.0,
                "1520358778000": 73.3008595989,
                "1520362378000": 74.0802292264,
                "1520365978000": 75.0,
                "1520369578000": 75.5428571429,
                "1520373178000": 76.0228571429,
                "1520376778000": 76.0,
                "1520380378000": 76.0,
                "1520383978000": 76.0
            }
        }
        ```

- `/api/hvac/day/setpoints`
    - returns: dictionary whose keys are zone names. Values are dictionaries from timestamp to a list of `[heating setpoint, cooling setpoint]` (in fahrenheit). Timestamps are in milliseconds since the Unix epoch
        ```json
        {
            "CentralZone": {
                "1520322785313": [73.0, 77.0]
            },
            "EastZone": {
                "1520322778354": [69.0, 72.0]
            },
            "NorthZone": {
                "1520322788082": [76.0, 80.0]
            },
            "SouthZone": {
                "1520322782137": [75.0, 79.0]
            }
        }
        ```
        ```
