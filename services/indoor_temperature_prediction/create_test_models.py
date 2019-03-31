# getting the utils file here

import os, sys
import datetime
import pytz

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

import time
from pathlib import Path
import pickle

import xbos_services_getter as xsg
import process_indoor_data as pid


def store_data(data, building, zone):
    data_dir = Path.cwd() / "services_data"
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    file_path = data_dir / (building + "_" + zone + ".pkl")

    with open(str(file_path), "wb") as f:
        pickle.dump(data, f)


def load_data(building, zone):
    data_dir = Path.cwd() / "services_data"
    if not os.path.isdir(data_dir):
        return None

    file_path = data_dir / (building + "_" + zone + ".pkl")
    if not os.path.isfile(file_path):
        return None

    with open(str(file_path), "rb") as f:
        return pickle.load(f)


def create_model(building, zone, start, end, prediction_window, raw_data_granularity, train_ratio, is_second_order,
                 use_occupancy,
                 curr_action_timesteps, prev_action_timesteps, method):
    """Creates a model with the given specifications.

    :param building: (string) building name
    :param zone: (string) zone name
    :param start: (datetime timezone aware) start of the dataset used
    :param end: (datetime timezone aware) start of the dataset used
    :param prediction_window: (str) number of seconds between predictions
    :param raw_data_granularity: (str) the window size of the raw data. needs to be less than prediction_window.
    :param train_ratio: (float) in (0, 1). the ratio in which to split train and test set from the given dataset. The train set comes before test set in time.
    :param is_second_order: (bool) Whether we are using second order in temperature.
    :param curr_action_timesteps: (int) The order of the current action. Set 0 if there should only be one action.
    :param prev_action_timesteps: (int) The order of the previous action. Set 0 if there should only be one prev action.
        Set -1 if it should not be used at all.
    :param method: (str) ["OLS", "random_forest", "LSTM"] are the available methods so far
    :param rmse_series: np.array the rmse of the forecasting procedure.
    :param num_forecasts: (int) The number of forecasts which contributed to the RMSE.
    :param forecasting_horizon: (int seconds) The horizon used when forecasting.
    :return: trained sklearn.LinearRegression object.

    """
    seconds_prediction_window = xsg.get_window_in_sec(prediction_window)


    if method != "OLS":
        raise NotImplementedError("%s is not supported. Use OLS instead." % method)

    # Get data
    # TODO add check that the data we have stored is at least as long and has right prediction_window
    # TODO Fix how we deal with nan's. some zone temperatures might get set to -1.
    loaded_data = load_data(building, zone)
    if loaded_data is None:
        processed_data = pid.get_preprocessed_data(building, zone, start, end, prediction_window, raw_data_granularity)
        store_data(processed_data, building, zone)
    else:
        processed_data = loaded_data

    # add features
    processed_data = pid.indoor_data_cleaning(processed_data)
    if is_second_order:
        processed_data = pid.add_feature_last_temperature(processed_data)
    if curr_action_timesteps > 0 or prev_action_timesteps > 0:
        processed_data = pid.convert_categorical_action(processed_data, num_start=curr_action_timesteps,
                                                        num_end=prev_action_timesteps,
                                                        interval_thermal=seconds_prediction_window)

    # split data into training and test sets
    N = processed_data.shape[0]  # number of datapoints
    train_data = processed_data.iloc[:int(N * train_ratio)]
    test_data = processed_data.iloc[int(N * train_ratio):]

    # which columns to drop for training and testing
    columns_to_drop = ["dt", "action_duration"]
    if curr_action_timesteps != 0:
        columns_to_drop.append("action")
    if prev_action_timesteps != 0 or prev_action_timesteps == -1:
        columns_to_drop.append("action_prev") # TODO we might want to use this as a feature. so don't set to -1...
    if not use_occupancy:
        columns_to_drop.append("occ")

    # train data
    train_data = train_data[train_data["dt"] == seconds_prediction_window]
    train_data = train_data.drop(columns_to_drop, axis=1)

    train_y = train_data["t_next"].interpolate(method="time")
    train_X = train_data.drop(["t_next"], axis=1).interpolate(method="time")

    # test data
    test_data = test_data[test_data["dt"] == seconds_prediction_window]
    test_data = test_data.drop(columns_to_drop, axis=1)

    test_y = test_data["t_next"].interpolate(method="time")
    test_X = test_data.drop(["t_next"], axis=1).interpolate(method="time")

    # Make OLS model
    reg = LinearRegression().fit(train_X, train_y)
    return reg, test_X.columns

