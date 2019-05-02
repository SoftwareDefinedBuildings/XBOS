import xbos_services_getter as xsg
import numpy as np


"""Thermostat class to model temperature change."""
class Tstat:
    def __init__(self, building, zone, temperature, last_temperature=None):
        self.temperature = temperature
        self.last_temperature = last_temperature
        self.indoor_temperature_prediction_stub = xsg.get_indoor_temperature_prediction_stub()
        self.error = {}
        for action in [xsg.NO_ACTION, xsg.HEATING_ACTION, xsg.COOLING_ACTION]:
            mean, var = xsg.get_indoor_temperature_prediction_error(self.indoor_temperature_prediction_stub,
                                                                    building,
                                                                    zone,
                                                                    action)
            self.error[action] = {"mean": mean, "var": var}

    def next_temperature(self, action):
        self.temperature += 1 * (action == 1) - 1 * (action == 2) + np.random.normal(self.error[action]["mean"],
                                                                                     self.error[action]["var"])
        return self.temperature

    def reset(self, temperature, last_temperature=None):
        self.temperature = temperaure
        self.last_temperature = last_temperature

class OutdoorThermostats:
    pass