import xbos_services_getter as xsg
import numpy as np

"""Thermostat class to model temperature change.
Note, set STANDARD fields to specify error for actions which do not have enough data for valid predictions. """
class Tstat:
    STANDARD_MEAN = 0
    STANDARD_VAR = 0
    STANDARD_UNIT = "F"

    def __init__(self, building, zone, temperature, last_temperature=None, suppress_not_enough_data_error=False):
        self.temperature = temperature
        self.last_temperature = last_temperature
        self.indoor_temperature_prediction_stub = xsg.get_indoor_temperature_prediction_stub()
        self.error = {}
        for action in [xsg.NO_ACTION, xsg.HEATING_ACTION, xsg.COOLING_ACTION]:
            try:
                mean, var, unit = xsg.get_indoor_temperature_prediction_error(self.indoor_temperature_prediction_stub,
                                                                              building,
                                                                              zone,
                                                                              action)
            except:
                if not suppress_not_enough_data_error:
                    raise  Exception("ERROR: Tstat for building: '{0}' and zone: '{1}' did not receive error data from "
                      "indoor_temperature_prediction microservice for action: '{2}'.")

                print("WARNING: Tstat for building: '{0}' and zone: '{1}' did not receive error data from "
                      "indoor_temperature_prediction microservice for action: '{2}' and is now using STANDARD error.".format(building, zone, action))
                mean, var, unit = Tstat.STANDARD_MEAN, Tstat.STANDARD_VAR, Tstat.STANDARD_UNIT

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
