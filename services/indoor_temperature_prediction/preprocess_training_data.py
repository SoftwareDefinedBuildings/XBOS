# getting the utils file here
import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
xbos_services_path = os.path.dirname(os.path.dirname(FILE_PATH))
sys.path.append(xbos_services_path)
sys.path.append(xbos_services_path + "/microservices_wrapper")
import microservices_wrapper as mw
import utils3 as utils
import datetime
import calendar
import pytz
import numpy as np
import pandas as pd

# UNRELATED THOUGHTS: Should any preprocessing happen in outdoor temperatures microservice?
# YES. And there should be an option to preprocess in inddoor data service with a trained thermal model.


def get_training_data(building, zone, start, end, window, raw_data_granularity="1m"):
    """
    Get training data to use for indoor temperature prediction.
    :param building: (str) building name
    :param zone: (str) zone name
    :param start: (datetime timezone aware)
    :param end: (datetime timezone aware)
    :param window: (str) the intervals in which to split data.
    :param raw_data_granularity: (str) the intervals in which to get raw indoor data.
    :return: pd.df index= start (inclusive) to end (not inclusive) with frequency given by window.
            col=["t_in", "action",  "t_out", "t_next", "occ", "t_prev", "action_duration", "last_action",
            "temperature_zone_...", "dt"]. TODO explain meaning of each feature somewhere.
    """
    # get indoor temperature and action for current zone
    indoor_historic_stub = mw.get_indoor_historic_stub()
    indoor_temperatures = mw.get_indoor_temperature_historic(indoor_historic_stub, building, zone, start, end,
                                                             raw_data_granularity)
    indoor_actions = mw.get_actions_historic(indoor_historic_stub, building, zone, start, end, raw_data_granularity)

    # get indoor temperature for other zones
    all_zones = utils.get_zones(building)
    all_other_zone_temperature_data = {}
    for iter_zone in all_zones:
        if iter_zone != zone:
            all_other_zone_temperature_data[iter_zone] = mw.get_indoor_temperature_historic(indoor_historic_stub,
                                                                 building, iter_zone, start, end, window)

    # Putting temperature and action data together.
    indoor_data = pd.concat([indoor_temperatures.to_frame(name="t_in"), indoor_actions.to_frame(name="action")], axis=1)
    indoor_data = preprocess_indoor_data(indoor_data, utils.get_window_in_sec(window))

    # Clean indoor data and add feature.
    indoor_data = indoor_data_cleaning(indoor_data, utils.get_window_in_sec(window))
    training_data = add_feature_last_temperature(indoor_data)

    # get historic outdoor temperatures
    outdoor_historic_stub = mw.get_outdoor_historic_stub()
    outdoor_historic_temperatures = mw.get_outdoor_temperature_historic(outdoor_historic_stub, building, start, end, window)

    # get occupancy
    occupancy_stub = mw.get_occupancy_stub()
    occupancy = mw.get_occupancy(occupancy_stub, building, zone, start, end, window)

    # add features
    training_data["t_out"] = [outdoor_historic_temperatures.loc[
                              idx: idx + datetime.timedelta(seconds=utils.get_window_in_sec(window))].mean() for idx in
                              training_data.index]

    training_data["occ"] = [occupancy.loc[
                              idx: idx + datetime.timedelta(seconds=utils.get_window_in_sec(window))].mean() for idx in
                              training_data.index]

    for iter_zone, iter_data in all_other_zone_temperature_data.items():
        training_data["temperature_zone_" + iter_zone] = [
            iter_data.loc[idx: idx + datetime.timedelta(seconds=utils.get_window_in_sec(window))].mean() for idx in
            training_data.index]

    return training_data


def add_feature_last_temperature(data):
    """Adding a feature which specifies what the previous temperature was "dt" seconds before the current
    datasample. Since data does not need be continious, we need a loop.
    :param: pd.df with cols: "t_in", "dt" and needs to be sorted by time index.
    returns pd.df with cols "t_last" added. """

    if data.shape[0] == 0:
        data["t_last"] = []
        return data

    last_temps = []

    last_temp = None
    curr_time = data.index[0]
    for index, row in data.iterrows():

        if last_temp is None:
            last_temps.append(row["t_in"])  # so the feature will be zero instead
        else:
            last_temps.append(last_temp)

        if curr_time == index:
            last_temp = row["t_in"]
            curr_time += datetime.timedelta(seconds=row["dt"])
        else:
            last_temp = None
            curr_time = index + datetime.timedelta(seconds=row["dt"])

    data["t_last"] = np.array(last_temps)
    return data

def add_action_dummy_variable(data):
    """
    Converting the action categorical variable to dummy variables (one hot encoding). Takes into account for how
    long the action has been going.
    :param data:
    :return:
    """


def indoor_data_cleaning(data, interval):
    """Fixes up the data. Makes sure we count two stage as single stage actions, don't count float actions,
     fill's nan's in action_duration and drops all datapoints which
    don't have dt equal to interval, sorts data by time index.
    :param data: pd.df col includes "action", "dt", "action_duration". "dt" and "action_duration"
    columns have string values. index should be timerseries.
    :param interval: int:seconds
    :return: cleaned data."""

    def f(x):
        if x == 0:
            return 0
        elif x == 2 or x == 5:
            return 2
        elif x ==1 or x == 3:
            return 1
        else:
            return -1

    data["action"] = data["action"].map(f)
    data = data[data["action"] != -1]

    # fill nans
    data = data.fillna(-1)  # set all nan values to negative one.
                            # Note: Previous action with -1 is counted as if no action happened before.

    # Filter by interval.
    data = data[data["dt"] == interval]

    data.sort_index()

    return data


def preprocess_indoor_data(indoor_data, interval):
    """Combines contigious data -- i.e. is contigious in time and has the same action.
    Every datapoint knows how many seconds ago the last change of action happened (action_duration)
    and knows what the last action was (last_action).
    :param zone_data: pd col=("action", "t_in"), Index needs to be continuous in time.
    :param interval: float:seconds The maximum length in seconds of a grouped data block.
    :returns: {zone: pd.df columns: 'time' (datetime), 't_in' (float), 't_next' (float),
    'dt' (int), 'action' (float), 'last_action' (float), 'action_duration' (int)}
    No nan values except potentially in last_action column -- means that we don't know the last action.
    """

    if indoor_data.shape[0] == 0:
        return None

    data_list = []

    first_row = indoor_data.iloc[0]

    # init our variables.
    start_time = indoor_data.index[0]
    last_time = start_time  # last valid time. To account for temperatures which are nan values.

    curr_action = first_row["action"]
    start_temperature = first_row["t_in"]

    # last not None temperature.
    last_temperature = start_temperature

    # whether the current datablock is valid. (datablock is a contigious grouping of same action datapoints)
    is_valid_block = not (np.isnan(curr_action) or np.isnan(start_temperature))

    # setting action start/end counters.
    curr_action_start = start_time
    last_action = np.nan  # Assume last action has been going on forever before current action.

    # start loop
    for index, row in indoor_data.iterrows():

        # if actions are None we just move on
        if np.isnan(curr_action) and np.isnan(row["action"]):
            continue

        # if action is the current action (we can assume that actions are valid, but starting temperatures may not be.)
        if curr_action == row["action"]:

            if not np.isnan(row["t_in"]):
                if index >= start_time + datetime.timedelta(seconds=interval):
                    # add datapoint and restart
                    if is_valid_block:
                        data_list.append({
                            'time': start_time,
                            't_in': start_temperature,
                            't_next': row["t_in"],
                            'dt': int((index - start_time).total_seconds()),
                            'action': curr_action,
                            'last_action': last_action,
                            'action_duration': int((index - curr_action_start).total_seconds())})

                    # restart fields
                    start_temperature = row["t_in"]
                    start_time = index
                    is_valid_block = not (np.isnan(curr_action) or np.isnan(start_temperature))

                # if not valid block but we have found a non-nan starting temperature, restart block
                if not is_valid_block:
                    start_temperature = row["t_in"]
                    start_time = index
                    is_valid_block = not (np.isnan(curr_action) or np.isnan(start_temperature))

                # remember last valid temperature with same action
                last_temperature = row["t_in"]
                last_time = index


            else:
                # if times match we set t_next to the last valid temperature and time
                if index >= start_time + datetime.timedelta(seconds=interval):
                    if is_valid_block:
                        data_list.append({
                            'time': start_time,
                            't_in': start_temperature,
                            't_next': last_temperature,
                            'dt': int((last_time - start_time).total_seconds()),
                            'action': curr_action,
                            'last_action': last_action,
                            'action_duration': int((last_time - curr_action_start).total_seconds())})

                    # restart fields. This will make it an invalid block
                    start_temperature = row["t_in"]
                    start_time = index
                    is_valid_block = not (np.isnan(curr_action) or np.isnan(start_temperature))

        # if action is not the current action
        else:
            if not np.isnan(row["t_in"]):
                if is_valid_block:
                    data_list.append({
                        'time': start_time,
                        't_in': start_temperature,
                        't_next': row["t_in"],
                        'dt': int((index - start_time).total_seconds()),
                        'action': curr_action,
                        'last_action': last_action,
                        'action_duration': int((index - curr_action_start).total_seconds())})
            else:
                if is_valid_block:
                    data_list.append({
                        'time': start_time,
                        't_in': start_temperature,
                        't_next': last_temperature,
                        'dt': int((last_time - start_time).total_seconds()),
                        'action': curr_action,
                        'last_action': last_action,
                        'action_duration': int((last_time - curr_action_start).total_seconds())})

            # restart the whole block.
            last_action = curr_action
            curr_action_start = index

            curr_action = row["action"]
            start_temperature = row["t_in"]
            start_time = index

            last_temperature = row["t_in"]
            last_time = index

            is_valid_block = not (np.isnan(curr_action) or np.isnan(start_temperature))

    # add last datapoint
    if start_time != indoor_data.index[-1] and is_valid_block:
        data_list.append({
            "time": start_time,
            't_in': start_temperature,
            't_next': last_temperature,
            'dt': int((last_time - start_time).total_seconds()),
            'action': curr_action,
            'last_action': last_action,
            'action_duration': int((last_time - curr_action_start).total_seconds())})

    # if no datapoints could be created, we return None.
    if data_list == []:
        return None

    preprocessed_indoor_data = pd.DataFrame(data_list).set_index('time')

    return preprocessed_indoor_data


if __name__ == "__main__":
    import time
    bldg = "ciee"
    zone = "HVAC_Zone_Southzone"
    end = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(hours=20)
    start = end - datetime.timedelta(days=5)

    getting_training_data_time = time.time()
    data = get_training_data(bldg, zone, start, end, "5m")
    print(data)
    print("Time to get training data:", time.time() - getting_training_data_time)

    # building = 'ciee'
    # zone = "HVAC_Zone_Northzone"
    #
    # end = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    # start = end - datetime.timedelta(hours=2)
    #
    # bw_client = Client()
    # bw_client.setEntityFromEnviron()
    # bw_client.overrideAutoChainTo(True)
    # hod_client = HodClient("xbos/hod", bw_client)
    # mdal_client = mdal.MDALClient("xbos/mdal")
    #
    # indoor = _get_raw_indoor_temperatures(building, zone, mdal_client, hod_client, start, end, "1m")
    # action = _get_raw_actions(building, zone, mdal_client, hod_client, start, end, "1m")
    # print(preprocess_thermal_data(indoor, action, 15))

    # ==== TESTS FOR PREPROCESSING ====
    # start = datetime.datetime(year=2018, month=5, day=1, hour=0, minute=0)
    #
    # # create test cases
    # test_cases = []
    #
    # tin = [np.nan, 2, 1]
    # action = [0, 1, 2]
    # test_cases.append([tin, action])
    #
    # tin = [1, np.nan, 2, 1]
    # action = [1, 0, 1, 2]
    # test_cases.append([tin, action])
    #
    # tin = []
    # action = []
    # test_cases.append([tin, action])
    #
    # tin = [-2]
    # action = [12]
    # test_cases.append([tin, action])
    #
    # tin = [1, 2, 3, 4, np.nan, 6, 7]
    # action = [0, 0, np.nan, 0, 0, 0, 0]
    # test_cases.append([tin, action])
    #
    # tin = [1, 2, 3, 4, np.nan, 6, 7]
    # action = [0, 0, np.nan, 0, 0, 2, 2]
    # test_cases.append([tin, action])
    #
    # tin = [np.nan, 2, 3, 4, np.nan, 6, 7]
    # action = [0, 0, np.nan, 0, 0, 2, 2]
    # test_cases.append([tin, action])
    #
    # tin = [1, 2, 3, 4, np.nan, 6, 7]
    # action = [np.nan, 0, np.nan, 0, 0, 2, 2]
    # test_cases.append([tin, action])
    #
    # action = [np.nan, 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 0, 0, 2, 2]
    # tin = list(range(len(action)))
    # test_cases.append([tin, action])
    #
    # tin = [1, np.nan, 3, 4, 5, 6, 7, 8, 9, 10]
    # action = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # test_cases.append([tin, action])
    #
    # for case in test_cases:
    #     tin = case[0]
    #     action = case[1]
    #     assert len(tin) == len(action)
    #     end = start + datetime.timedelta(minutes=len(tin) - 1)
    #
    #     test_data = pd.DataFrame(index=pd.date_range(start, end, freq="1T"), data={"t_in": tin, "action": action})
    #     print(test_data)
    #     print("processed", _preprocess_thermal_data(test_data, 5))
    #     print("")
    # # ==== END ====

