# XBOS Site-specific Dashboard

## Running

Use Python3

```
virtualenv venv
. venv/bin/activate
pip install -r requirements.txt
FLASK_APP=app.py flask run
```

Make sure you fill out `config.toml`; this requires making an account on [https://mortardata.org/](https://mortardata.org/)

## API Doc

### SVG endpoint

Put SVG files in `static/svg` and name them appropriately to the building. You can fetch the SVG content by doing a GET to `/svg/<building name>.svg`.

### DR Endpoints

- `/api/prediction/dr/<provider>`
    - Parameter:
        - `provider`: one of `pge`, `sce` depending on the site
    - Returns: list of (usually 3) upcoming days and the likelihood of a DR event on those days.
      The `likelihood` value takes on one of `no event`, `unlikely`, `possible`, `likely`, or `confirmed`.
        ```json
        {
            "days": [
                {
                    "date": 1533324092,
                    "likelihood": "unlikely"
                },
                {
                    "date": 1566624092,
                    "likelihood": "possible"
                },
            ]
        }
        ```

### Power Endpoints

All of these are for full building power/energy

- `/api/power/<last>/in/<bucketsize>`
    - Parameter:
        - `last`: one of `year`,`month`,`week`,`day`,`hour`
        - `bucketsize`: follows format `{number}{unit}`
            - `number`: 1,2, etc
            - `unit`: `m` (minute), `h` (hour), `d` (day)
            - OR specify just `month` to get month-aware divisions
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
            - OR specify just `month` to get month-aware divisions
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
- `/api/price`
    - Returns: TODO: how is pricing information encoded? maybe epoch start time mapped to price per kwh?
        ```json
        {
            "readings": {
                "1530550800000": .13,
                "1530557000000": .18,
                "1530565200000": .68,
                "1530579600000": .18,
            }
        }
        ```


### HVAC Endpoints

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

- `/api/hvac/day/in/<bucketsize>`
    - get current day of temperature data for each zone in `<bucketsize>`. Aggregates using mean
    - `bucketsize`: follows format `{number}{unit}`
        - `number`: 1,2, etc
        - `unit`: `m` (minute), `h` (hour)
    - examples:
        - `1h` (1 hour)
        - `15min` (1 minute)
    - returns: dictionary whose keys are zone names. Values are dictionaries with the following values. All timestamps are in milliseconds since the Unix epoch
        - `inside`: map of timestamp to value for inside air temperature in Fahrenheit
        - `outside`: map of timestamp to value for outside air temperature in Fahrenheit
        - `heating_setpoint`: map of timestamp to value for heating setpoint in Fahrenheit. Returned timestamps indicate when heating setpoint takes effect
        - `cooling_setpoint`: map of timestamp to value for cooling setpoint in Fahrenheit. Returned timestamps indicate when cooling setpoint takes effect
        - `state`: map of timestamp to value for HVAC state. Returned timestamps indicate when the HVAC state takes effect
        ```json
        {
            "EastZone": {
                "inside": {
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
                "outside": {
                    "1520322778000": 89.49,
                    "1520326378000": 89.2,
                    "1520329978000": 89.22,
                    "1520333578000": 89.29,
                    "1520337178000": 89.25,
                    "1520340778000": 89.26,
                    "1520344378000": 89.29,
                    "1520347978000": 89.52,
                    "1520351578000": 89.23,
                    "1520355178000": 89.62,
                    "1520358778000": 80.07,
                    "1520362378000": 80.35,
                    "1520365978000": 80.49,
                    "1520369578000": 80.64,
                    "1520373178000": 80.7,
                    "1520376778000": 80.8,
                    "1520380378000": 81.5,
                    "1520383978000": 82.13
                 },
                "heating_setpoint": {
                    "1520332782137": 75.0,
                    "1520330000000": 55.0,
                 },
                "cooling_setpoint": {
                    "1520322782137": 78.0,
                    "1520330000000": 85.0,
                 },
                 "state": {
                    "1520322778000": "heat stage 1",
                    "1520329978000": "off",
                    "1520358778000": "heat stage 1",
                    "1520365978000": "heat stage 2",
                    "1520369578000": "off",
                    "1520373178000": "heat stage 1"
                 },
            }
        }
        ```

- `/api/hvac/day/setpoints`
    - returns: dictionary whose keys are zone names. Values are dictionaries from timestamp to a list of `[heating setpoint, cooling setpoint]` (in fahrenheit). Timestamps are in milliseconds since the Unix epoch. This is sort of like the schedule
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

### Occupancy

- `/api/occupancy/<last>/in/<bucketsize>`
    - Parameter:
        - `last`: one of `year`,`month`,`week`,`day`,`hour`
        - `bucketsize`: follows format `{number}{unit}`
            - `number`: 1,2, etc
            - `unit`: `m` (minute), `h` (hour), `d` (day)
            - OR specify just `month` to get month-aware divisions
        - examples:
            - `30d` (30 days)
            - `1h` (1 hour)
    - Returns: JSON dictionary with key `readings`. Contains dictionary of timestamp (in milliseconds since Unix epoch) to value (in binary occupancy signal over the bucket period)
        ```json
        {
            "readings": {
                "1520283178000": 0,
                "1520286778000": 1,
                "1520290378000": 1,
                "1520293978000": 1,
                "1520297578000": 1,
                "1520301178000": 1,
                "1520304778000": 0,
                "1520308378000": 0,
                "1520311978000": 1,
                "1520315578000": 0,
                "1520319178000": 1,
                "1520322778000": 0,
                "1520326378000": 0,
                "1520329978000": 1,
                "1520333578000": 0,
                "1520337178000": 1,
                "1520340778000": 1,
                "1520344378000": 1,
                "1520347978000": 0,
                "1520351578000": 0,
                "1520355178000": 1,
                "1520358778000": 1,
                "1520362378000": 1,
                "1520365978000": 0
            }
        }
        ```


### Prediction Endpoints

- `/api/prediction/hvac/day/in/<bucketsize>`: Predictions for the *current* day (TODO: want for more than just today?)
    - Parameters:
        - `bucketsize`: follows format `{number}{unit}`
            - `number`: 1,2, etc
            - `unit`: `m` (minute), `h` (hour), `d` (day)
            - OR specify just `month` to get month-aware divisions
    - Returns: dictionary keyed by HVAC zone. Each zone has predictions delivered in a predefined prediction interval 
        - `inside`: inside temperature predictions at given interval
        - `outside`: outside temperature predictions at given interval
        - `heating_setpoint`: projected heating setpoint changes
        - `cooling_setpoint`: projected cooling setpoint changes
        - `state`: projected sequence of HVAC state changes
        ```json
        {
            "EastZone": {
                "inside": {
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
                "outside": {
                    "1520322778000": 89.49,
                    "1520326378000": 89.2,
                    "1520329978000": 89.22,
                    "1520333578000": 89.29,
                    "1520337178000": 89.25,
                    "1520340778000": 89.26,
                    "1520344378000": 89.29,
                    "1520347978000": 89.52,
                    "1520351578000": 89.23,
                    "1520355178000": 89.62,
                    "1520358778000": 80.07,
                    "1520362378000": 80.35,
                    "1520365978000": 80.49,
                    "1520369578000": 80.64,
                    "1520373178000": 80.7,
                    "1520376778000": 80.8,
                    "1520380378000": 81.5,
                    "1520383978000": 82.13
                 },
                "heating_setpoint": {
                    "1520332782137": 75.0,
                    "1520330000000": 55.0,
                 },
                "cooling_setpoint": {
                    "1520322782137": 78.0,
                    "1520330000000": 85.0,
                 },
                 "state": {
                    "1520322778000": "heat stage 1",
                    "1520329978000": "off",
                    "1520358778000": "heat stage 1",
                    "1520365978000": "heat stage 2",
                    "1520369578000": "off",
                    "1520373178000": "heat stage 1"
                 },
            }
        }
        ```

- `/api/simulation/<drlambda>/<date>/<zone>`
    ```json
    {
        "hvac_zone_back_hallway": {
            "cooling": {
                "1565938800000": 30,
                    "1565939700000": 30,
                    "1565940600000": 30,
                    "1565941500000": 30,
                    "1565942400000": 30
                },
                "heating": {
                    "1565938800000": 30,
                    "1565939700000": 30,
                    "1565940600000": 30,
                    "1565941500000": 30,
                    "1565942400000": 30
                },
                "inside": {
                    "1565938800000": 66.0,
                    "1565939700000": 65.75279985906522,
                    "1565940600000": 65.43783332903159,
                    "1565941500000": 65.25098112112512,
                    "1565942400000": 65.45344733595263
                },
                "outside": {
                    "1565938800000": 30,
                    "1565939700000": 30,
                    "1565940600000": 30,
                    "1565941500000": 30,
                    "1565942400000": 30
                },
                "state": {
                    "1565938800000": "off",
                    "1565939700000": "off",
                    "1565940600000": "off",
                    "1565941500000": "off",
                    "1565942400000": "off"
                }
        },
        "hvac_zone_second": { // ... }
    }
    ```
