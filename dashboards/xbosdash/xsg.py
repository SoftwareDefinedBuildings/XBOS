import datetime
import pendulum
import pytz
import numpy as np
import pandas as pd
import toml
from xbos_services_getter import xbos_services_getter as xsg

config = toml.load(open('config.toml'))

ADDRESS=config['Microservices']['url']

price_stub = xsg.get_price_stub(ADDRESS)
optimizer_stub = xsg.get_optimizer_stub(ADDRESS)
building_zone_names_stub = xsg.get_building_zone_names_stub(ADDRESS)

def get_tariff_and_utility(building):
    return xsg.get_tariff_and_utility(price_stub, building)

def get_price(building, start, end):
    prices = xsg.get_price(price_stub, building, 'ENERGY', start, end, '1h')
    print(prices)
    return prices

def get_zones(building):
    return xsg.get_zones(building_zone_names_stub, building)

"""Thermostat class to model temperature change."""
class Tstat:
    def __init__(self, building, zone, temperature, last_temperature=None):
        self.temperature = temperature
        self.last_temperature = last_temperature
        self.indoor_temperature_prediction_stub = xsg.get_indoor_temperature_prediction_stub(ADDRESS)
        self.error = {}
        for action in [xsg.NO_ACTION, xsg.HEATING_ACTION, xsg.COOLING_ACTION]:
            mean, var, unit = xsg.get_indoor_temperature_prediction_error(self.indoor_temperature_prediction_stub,
                                                                    building,
                                                                    zone,
                                                                    action)
            self.error[action] = {"mean": mean, "var": var}

    def next_temperature(self, action):
        self.last_temperature = self.temperature
        self.temperature += 1 * (action == 1) - 1 * (action == 2) + np.random.normal(self.error[action]["mean"],
                                                                                     self.error[action]["var"])
        return self.temperature

    def reset(self, temperature, last_temperature=None):
        self.temperature = temperature
        self.last_temperature = last_temperature

class OutdoorThermostats:
    pass

def simulation(building, start, end, horizon, lambda_val, zone=None):
    all_zones = get_zones(building)
    use_zones = [zone] if zone is not None else all_zones
    #zonename = all_zones[0]
    print(building, start, end, horizon, lambda_val)
    results = {}
    for zonename in use_zones:
        starting_temperatures = {zone: 66. for zone in all_zones}
        # 15 minutes here is the simulated step
        res = xsg.get_mpc_simulation(optimizer_stub, building, [zonename], start, end, '15m', horizon, lambda_val, starting_temperatures)
        dates = pd.date_range(start, end, freq='15T')
        actions, temperatures = res
        # we pad the actions with an 'off'
        actions = list(actions[0][zonename].actions) + [0]
        d = {
                'time': dates,
                'actions': actions,
                'temperatures': temperatures[0][zonename].temperatures,
            }
        print({k: len(v) for k,v in d.items()})
        df = pd.DataFrame.from_dict(d)
        df = df.set_index(pd.to_datetime(df.pop('time')))
        df = df.resample('15T').max()
        results[zonename] = df
    return results

if __name__=='__main__':
    from datetime import datetime, timedelta
    TZ=pytz.timezone('US/Pacific')
    #start = datetime(year=2016,day=1,month=1,hour=0,tzinfo=TZ)
    start = datetime.now(TZ)-timedelta(days=2)
    end = datetime.now(TZ)-timedelta(days=1)
    # 1 zone at a time
    # (start, end): beginning and end of the simulated interval
    # horizon 4h is good
    res = simulation('avenal-movie-theatre', start, end, '4h', 0.9, 'hvac_zone_lobby')
