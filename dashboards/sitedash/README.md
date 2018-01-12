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

- `/api/power/daily/{num}`:
    - returns:
        ```json
        {
            "readings": [
                # starts with timestamp of the beginning of the day
                {1515443111: 70.0},
                {1515443101: 71.0},
                {1515443091: 79.0},
                {1515443081: 80.0},
            ]
        }
        ```
    - parameters:
        - `{num}`: number of days to fetch
    - implementation notes:
        - want to align this to beginning of day

- `/api/power/weekly/{num}`:
    - returns:
        ```json
        {
            "readings": [
                # starts with timestamp of the beginning of the week
                {1515443111: 70.0},
                {1515443101: 71.0},
                {1515443091: 79.0},
                {1515443081: 80.0},
            ]
        }
        ```
    - parameters:
        - `{num}`: number of weeks to fetch
    - implementation notes:
        - want to align this to Monday (instead of just "past 7 days"), so query will need to figure out the date of "last Monday"

- `/api/power/monthly/{num}`:
    - returns:
        ```json
        {
            "readings": [
                # starts with timestamp of the beginning of the month
                {1515443111: 70.0},
                {1515443101: 71.0},
                {1515443091: 79.0},
                {1515443081: 80.0},
            ]
        }
        ```
    - parameters:
        - `{num}`: number of months to fetch
    - implementation notes:
        - want to align this to first of month

- `/api/power`:
    - latest power readings for full building. GET to get the latest reading
    - returns:
        ```json
        {
            "demand": 7234.3
        }
        ```

### HVAC Endpoints

- `/api/hvac`:
    - stream current HVAC state over websockets
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
