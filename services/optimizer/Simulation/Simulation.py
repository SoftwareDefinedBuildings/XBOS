import time

import datetime
import pytz
import calendar
import itertools
import pandas as pd

import datetime
import sys

import numpy as np
import os
import pandas as pd
import pytz


import xbos_services_getter as xsg

from Optimizers.MPC.MPC import MPC
from Optimizers.MPC.MPC import Node
from DataManager.DataManager import DataManager
from Thermostat import Tstat

# Simulation Class for MPC. Stops simulation when the current time is equal to the end.
class SimulationMPC():

    def __init__(self, building, zones, lambda_val, start, end, forecasting_horizon, window, tstats, non_contrallable_data=None):

        assert xsg.get_window_in_sec(forecasting_horizon) % xsg.get_window_in_sec(window) == 0

        self.building = building
        self.zones = zones
        self.window = window
        self.lambda_val = lambda_val

        self.forecasting_horizon = forecasting_horizon
        self.delta_forecasting_horizon = datetime.timedelta(seconds=xsg.get_window_in_sec(forecasting_horizon))

        self.delta_window = datetime.timedelta(seconds=xsg.get_window_in_sec(window))

        # Simulation end is when current_time reaches end and end will become the end of our data.
        self.simulation_end = end
        end += self.delta_forecasting_horizon

        self.DataManager = DataManager(building, zones, start, end, window, non_contrallable_data)



        self.tstats = tstats# dictionary of simulator object with key zone. has functions: current_temperature, next_temperature(action)

        self.current_time = start
        self.current_time_step = 0

        self.actions = {iter_zone: [] for iter_zone in self.zones} # {zone: [ints]}
        self.temperatures = {iter_zone: [self.tstats[iter_zone].temperature] for iter_zone in self.zones} # {zone: [floats]}


    def step(self):

        # call
        start_mpc = self.current_time
        end_mpc = self.current_time + self.delta_forecasting_horizon
        non_controllable_data = {
            "comfortband": {iter_zone: self.DataManager.comfortband[iter_zone].loc[start_mpc:end_mpc] for iter_zone in self.zones},
            "do_not_exceed": {iter_zone: self.DataManager.do_not_exceed[iter_zone].loc[start_mpc:end_mpc] for iter_zone in self.zones},
            "occupancy": {iter_zone: self.DataManager.occupancy[iter_zone].loc[start_mpc:end_mpc] for iter_zone in self.zones},
            "outdoor_temperature": self.DataManager.outdoor_temperature.loc[start_mpc:end_mpc]
        }

        op = MPC(self.building, self.zones, start_mpc, end_mpc, self.window, self.lambda_val, non_controllable_data=non_controllable_data,
                 debug=False)

        root = Node({iter_zone: self.tstats[iter_zone].temperature for iter_zone in self.zones}, 0)

        root = op.shortest_path(root)
        best_action = op.g.node[root]["best_action"]


        # given the actions, update simulation of temperature.
        # increment time

        self.current_time += self.delta_window
        self.current_time_step += 1

        for iter_zone in self.zones:
            # advances temperature and saves it
            self.temperatures[iter_zone].append(self.tstats[iter_zone].next_temperature(best_action[iter_zone]))
            self.actions[iter_zone].append(best_action[iter_zone])

        return root

    def run(self):
        while self.current_time < self.simulation_end:
            self.step()



if __name__ == "__main__":
    forecasting_horizon = "4h"

    end = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(
        seconds=xsg.get_window_in_sec(forecasting_horizon))
    end = end.replace(microsecond=0)
    start = end - datetime.timedelta(hours=6)

    print(start)
    print(start.timestamp())
    building = "avenal-animal-shelter"
    zones = ["hvac_zone_shelter_corridor"]
    window = "15m"
    lambda_val = 0.995
    tstats = {iter_zone: Tstat(building, iter_zone, 75) for iter_zone in zones}

    simulation = SimulationMPC(building, zones, lambda_val, start, end, forecasting_horizon, window, tstats)

    t = time.time()
    simulation.run()
    print(time.time() - t)
