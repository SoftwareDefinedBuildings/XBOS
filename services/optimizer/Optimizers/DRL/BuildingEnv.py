

import numpy as np
import xbos_services_getter as xsg

from DataManager.DataManager import DataManager
from Thermostat import Tstat

import gym, ray
from gym.spaces import Box, Discrete, Tuple

INF_REWARD = 1e3

class BuildingEnv(gym.Env):

    def __init__(self, env_config):

        self.DataManager = DataManager(env_config["building"], env_config["zones"],
                                       env_config["start"], env_config["end"], env_config["window"])

        self.start = start
        self.unix_start = start.timestamp() * 1e9
        self.end = end
        self.unix_end = end.timestamp() * 1e9
        self.window = window  # timedelta string

        self.building = building
        self.zones = zones

        self.lambda_val = env_config["lambda_val"]

        # assert self.zones == all zones in building. this is because of the thermal model needing other zone temperatures.

        self.curr_timestep = 0

        self.indoor_starting_temperatures = env_config[
            "indoor_starting_temperatures"]  # to get starting temperatures [last, current]
        self.outdoor_starting_temperature = env_config["outdoor_starting_temperature"]

        self.tstats = {}
        for iter_zone in self.zones:
            self.tstats[iter_zone] = Tstat(self.building, iter_zone,
                                           self.indoor_starting_temperatures[iter_zone]["current"],
                                           last_temperature=self.indoor_starting_temperatures[iter_zone]["last"])

        assert 60 * 60 % xsg.get_window_in_sec(self.window) == 0  # window divides an hour
        assert (self.end - self.start).total_seconds() % xsg.get_window_in_sec(
            self.window) == 0  # window divides the timeframe

        # the number of timesteps
        self.num_timesteps = int((self.end - self.start).total_seconds() / xsg.get_window_in_sec(self.window))

        self.unit = env_config["unit"]
        assert self.unit == "F"

        # all zones current and last temperature = 2*num_zones
        # building outside temperature -> make a class for how this behaves = 1
        # timestep -> do one hot encoding of week, day, hour, window  \approx 4 + 7 + 24 + 60*60 / window
        low_bound = [32] * 2 * len(
            self.zones)  # we could use parametric temperature bounds... for now we will give negative inft reward
        low_bound += [-100] # for outside temperature we cannot gurantee much
        
        high_bound = [100] * 2 * len(self.zones)
        low_bound += [200]  # for outside temperature we cannot gurantee much

        low_bound += [0] * (self.num_timesteps + 1)  # total timesteps plus the final timestep which wont be executed
        high_bound += [1] * (self.num_timesteps + 1)  # total timesteps plus the final timestep which wont be executed

        self.observation_space = Box(
            low=np.array(low_bound), high=np.array(high_bound), dtype=np.float32)

        self.action_space = Tuple((Discrete(3),) * len(self.zones))

        self.reset()

    def reset(self):
        self.curr_timestep = 0

        for iter_zone in self.zones:
            self.tstats[iter_zone].reset(self.indoor_starting_temperatures[iter_zone]["current"],
                                         last_temperature=self.indoor_starting_temperatures[iter_zone]["last"])
        self.outdoor_temperature = self.outdoor_starting_temperature

        return self.create_curr_obs()  # obs

    def step(self, action):

        self.curr_timestep += 1

        # if we reach the end time.
        if self.curr_timestep == self.num_timesteps:
            return self.create_curr_obs(), 0, True, {}

        # find what new temperature would be. use thermal model with uncertainty. use reset if exceeding
        # do_not_exceed. can't force it to take a different action anymore.

        # update temperatures
        for i, iter_zone in enumerate(self.zones):
            self.tstats[iter_zone].next_temperature(action[i])
            self.outdoor_temperature += np.random.normal()  # TODO we should make a thermostat for the outdoor temperature.

        # check that in saftey temperature band
        for iter_zone in self.zones:
            curr_safety = self.DataManager.do_not_exceed[iter_zone].iloc[self.curr_timestep]
            if not (curr_safety["t_low"] <= self.tstats[iter_zone].temperature <= curr_safety["t_high"]):
                return self.create_curr_obs(), -INF_REWARD, True, {}  # TODO do we want to add info?

        # get reward by calling discomfort and consumption model ...
        reward = self.get_reward(action)

        return self.create_curr_obs(), reward, False, {}  # obs, reward, done, info

    def get_reward(self, action):
        """Get the reward for the given action with the current observation parameters."""
        # get discomfort across edge
        discomfort = {}
        for iter_zone in self.zones:
            # TODO Check this again since we are a timestep ahead and we want average comfortband and average occupancy over the edge.
            curr_comfortband = self.DataManager.comfortband[iter_zone].iloc[self.curr_timestep]
            curr_occupancy = self.DataManager.occupancy[iter_zone].iloc[self.curr_timestep]
            curr_tstat = self.tstats[iter_zone]
            average_edge_temperature = (curr_tstat.temperature + curr_tstat.last_temperature) / 2.

            discomfort[iter_zone] = self.DataManager.get_discomfort(
                self.building, average_edge_temperature,
                curr_comfortband["t_low"], curr_comfortband["t_high"],
                curr_occupancy)

        # Get consumption across edge
        price = 1  # self.prices.iloc[root.timestep] TODO also add right unit conversion, and duration
        consumption_cost = {self.zones[i]: price * self.DataManager.hvac_consumption[self.zones[i]][action[i]]
                            for i in range(len(self.zones))}

        cost = ((1 - self.lambda_val) * (sum(consumption_cost.values()))) + (
                self.lambda_val * (sum(discomfort.values())))
        return -cost

    def create_curr_obs(self):
        return self._create_obs(self.tstats, self.outdoor_temperature, self.curr_timestep)

    def _create_obs(self, tstats, outdoor_temperature, curr_timestep):
        obs = np.zeros(self.observation_space.low.shape)
        idx = 0
        for iter_zone in self.zones:
            obs[idx] = tstats[iter_zone].last_temperature
            idx += 1
            obs[idx] = tstats[iter_zone].temperature
            idx += 1
        obs[idx] = outdoor_temperature
        idx += 1

        obs[idx + curr_timestep] = 1

        return obs

if __name__ == "__main__":
    import numpy as np
    import gym
    from ray.rllib.models import FullyConnectedNetwork, Model, ModelCatalog
    from gym.spaces import Discrete, Box

    import ray
    from ray import tune
    from ray.tune import grid_search

    import datetime
    import pytz

    start = datetime.datetime(year=2019, month=1, day=1).replace(tzinfo=pytz.utc)
    end = start + datetime.timedelta(days=1)
    window = "15m"
    building = "avenal-animal-shelter"
    zones = ["hvac_zone_shelter_corridor"]
    indoor_starting_temperatures = {iter_zone: {"last": 70, "current": 71} for iter_zone in zones}
    outdoor_starting_temperature = 60
    unit = "F"
    lambda_val = 0.999

    config = {
        "start": start,
        "end": end,
        "window": window,
        "building": building,
        "zones": zones,
        "indoor_starting_temperatures": indoor_starting_temperatures,
        "outdoor_starting_temperature": outdoor_starting_temperature,
        "unit": unit,
        "lambda_val": lambda_val
    }

    ray.init()
    # Can also register the env creator function explicitly with:
    # register_env("corridor", lambda config: SimpleCorridor(config))
    # ModelCatalog.register_custom_model("my_model", CustomModel)
    tune.run(
        "PPO",
        stop={
            "timesteps_total": 1e6,
        },
        config={
            "env": BuildingEnv,  # or "corridor" if registered above
            "lr": grid_search([1e-2, 1e-4, 1e-6]),  # try different lrs
            "num_workers": 1,  # parallelism
            "env_config": config,
        },
    )


    # e = BuildingEnv(config)
    # print(e.step([0]))