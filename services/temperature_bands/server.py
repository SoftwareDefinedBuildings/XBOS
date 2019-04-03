from concurrent import futures
import time
import grpc
import temperature_bands_pb2
import temperature_bands_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


# getting the utils file here
import os, sys
import xbos_services_utils3 as utils
import datetime
import pytz
import numpy as np
import pandas as pd
import yaml
import traceback

from pathlib import Path

DAYS_IN_WEEK = 7

TEMPERATURE_BANDS_DATA_PATH = Path(os.environ["TEMPERATURE_BANDS_DATA_PATH"])
TEMPERATURE_BANDS_HOST_ADDRESS = os.environ["TEMPERATURE_BANDS_HOST_ADDRESS"]


def _get_temperature_band_config(building, zone):
    band_path = str(TEMPERATURE_BANDS_DATA_PATH / building / (zone + ".yml"))

    if os.path.exists(band_path):
        with open(band_path, "r") as f:
            try:
                config = yaml.load(f)
            except yaml.YAMLError:
                return None, "yaml could not read file at: %s" % band_path
    else:
        return None, "consumption file could not be found. path: %s." % band_path

    return config, None


def _get_week_comfortband(building, zone, date, interval):
    """
    Gets the whole comfortband from the zone configuration file. Correctly Resamples the data according to interval
    :param date: The date for which we want to start the week. Timezone aware.
    :param interval: int:seconds. The interval/frequency of resampling. Has to be such that 60 % interval == 0
    :return: pd.df (col = "t_low", "t_high") with time_series index for the date provided and in timezone aware and in timezone of data input.
    """

    config, err = _get_temperature_band_config(building, zone)
    if config is None:
        return None, err

    # Set the date to the controller timezone.
    building_date = date.astimezone(tz=pytz.timezone(config["tz"]))
    weekday = building_date.weekday()

    list_data = []

    comfortband_data = config["comfortband"]

    df_do_not_exceed, err = _get_week_do_not_exceed(building, zone, building_date, interval)
    if df_do_not_exceed is None:
        return None, err

    # Note, we need to get a day before the start and after the end of the week to correctly resample due to timezones.
    for i in range(DAYS_IN_WEEK + 2):
        curr_weekday = (weekday + i - 1) % DAYS_IN_WEEK
        curr_day = building_date + datetime.timedelta(days=i - 1)

        curr_idx = []
        curr_comfortband = []

        weekday_comfortband = np.array(comfortband_data[curr_weekday])

        for interval_comfortband in weekday_comfortband:
            start, end, t_low, t_high = interval_comfortband
            start = utils.combine_date_time(start, curr_day)

            if t_low is None or t_low == "None":
                interval_safety = df_do_not_exceed[start-datetime.timedelta(seconds=interval):start]
                t_low = interval_safety["t_low"].mean() # TODO We want mean weighter by duration. Fine approximation for now

            if t_high is None or t_high == "None":
                interval_safety = df_do_not_exceed[start-datetime.timedelta(seconds=interval):start]
                t_high = interval_safety["t_high"].mean()


            curr_idx.append(start)
            curr_comfortband.append({"t_low": float(t_low),
                                       "t_high": float(t_high)})

        list_data.append(pd.DataFrame(index=curr_idx, data=curr_comfortband))

    df_comfortband = pd.concat(list_data)

    df_comfortband = df_comfortband.tz_convert(date.tzinfo)

    rounded_date = utils.decrement_to_start_of_day(date, interval)

    df_comfortband = utils.smart_resample(df_comfortband, rounded_date, rounded_date+datetime.timedelta(days=7), interval, "pad")

    return df_comfortband, None


def _get_week_do_not_exceed(building, zone, date, interval):
    """
    Gets the whole do_not_exceed from the zone configuration file. Correctly Resamples the data according to interval
    :param date: The date for which we want to start the week. Timezone aware.
    :param interval: float:seconds. The interval/frequency of resampling. Has to be such that 60 % interval == 0
    :return: pd.df (col = "t_low", "t_high") with time_series index for the date provided and in timezone aware and in timezone of data input.
    """

    config, err = _get_temperature_band_config(building, zone)

    if config is None:
        return None, err

    # Set the date to the controller timezone.
    building_date = date.astimezone(tz=pytz.timezone(config["tz"]))
    weekday = building_date.weekday()

    list_data = []

    do_not_exceed_data = config["do_not_exceed"]

    # Note, we need to get a day before the start and after the end of the week to correctly resample due to timezones.
    for i in range(DAYS_IN_WEEK + 2):
        curr_weekday = (weekday + i - 1) % DAYS_IN_WEEK
        curr_day = building_date + datetime.timedelta(days=i - 1)

        curr_idx = []
        curr_do_not_exceed = []

        weekday_do_not_exceed = np.array(do_not_exceed_data[curr_weekday])

        for interval_do_not_exceed in weekday_do_not_exceed:
            start, end, t_low, t_high = interval_do_not_exceed
            start = utils.combine_date_time(start, curr_day)

            curr_idx.append(start)
            curr_do_not_exceed.append({"t_low": float(t_low),
                                       "t_high": float(t_high)})

        list_data.append(pd.DataFrame(index=curr_idx, data=curr_do_not_exceed))

    df_do_not_exceed = pd.concat(list_data)

    df_do_not_exceed = df_do_not_exceed.tz_convert(date.tzinfo)

    rounded_date = utils.decrement_to_start_of_day(date, interval)

    df_do_not_exceed = utils.smart_resample(df_do_not_exceed, rounded_date, rounded_date+datetime.timedelta(days=7), interval, "pad")

    return df_do_not_exceed, None


def get_band(building, zone, start, end, interval, type_band):
    """Gets the comfortband/do_noteceed band of a zone from start to end in interval minutes frequency
    :param building: string
    :param zone: string
    :param start: datetime. timezone aware
    :param end: datetime. timezone aware.
    :param interval: int:seconds. 24*60*60 % interval == 0
    :param type_band: string ["comfortband", "do_not_exceed"] decides which setpoints to get.
    :return:

    NOTE: If (end-start).total_seconds % interval != 0, then end is rounded down to next closest
    such that this condition is satisfied. New end will also not be inclusive.
    """

    if type_band == "comfortband":
        first_seven_days, err = _get_week_comfortband(building, zone, start, interval)
    elif type_band == "do_not_exceed":
        first_seven_days, err = _get_week_do_not_exceed(building, zone, start, interval)
    else:
        return None, "Invalid method given for band."

    if first_seven_days is None:
        return None, err

    first_seven_days_start = first_seven_days.index[0]
    first_seven_days_end = first_seven_days_start + datetime.timedelta(days=DAYS_IN_WEEK)

    if end < first_seven_days_end:
        return first_seven_days[start:end][:-1], None

    # get band for the day after the first 7 days we found.
    remaining_data = []

    for i in range((end - first_seven_days_end).days + 1):

        curr_offset = i % DAYS_IN_WEEK

        curr_time = first_seven_days_end + datetime.timedelta(days=i)

        curr_data = first_seven_days[first_seven_days_start + datetime.timedelta(days=curr_offset):
                                     first_seven_days_start + datetime.timedelta(days=curr_offset + 1)][:int(24*60*60/interval)]

        curr_start_date = curr_time
        curr_end_date = curr_start_date + datetime.timedelta(days=1)
        date_range = pd.date_range(start=curr_start_date, end=curr_end_date, freq=str(interval/60.) + "T")[:-1]
        curr_data.index = date_range

        remaining_data.append(curr_data)

    band_series = pd.concat([first_seven_days] + remaining_data)

    return band_series[start:end][:-1], None


def get_comfortband(request):
    """Returns comfortband data for a given request or None."""

    start_time = time.time()

    print("received request:", request.building, request.zone, request.start, request.end, request.window, request.unit)
    duration = utils.get_window_in_sec(request.window)

    request_length = [len(request.building), len(request.zone), request.start, request.end,
                      duration]

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    # if request.end > int(time.time() * 1e9):
    #     return None, "invalid request, end date is in the future. Now: %d and end: %d" % (
    #     time.time() * 1e9, request.end)
    if request.start >= request.end:
        return None, "invalid request, start date is after end date."
    if request.start < 0 or request.end < 0:
        return None, "invalid request, negative dates"
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"
    if request.unit != "F":
        return None, "only fahrenheit support."
    if 60*60 % duration != 0:
        return None, "window is not a factor of an hour (60(min)*60(sec)%window != 0). e.g. 15min is a factor but 25 is not."

    start_datetime = datetime.datetime.utcfromtimestamp(
                                           float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_datetime = datetime.datetime.utcfromtimestamp(
                                           float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    error_checking_time = time.time()

    comfortband, err = get_band(request.building, request.zone, start_datetime, end_datetime, duration, "comfortband")
    if comfortband is None:
        return None, err

    comfortband_time = time.time()

    grpc_comfortband = []
    for index, row in comfortband.iterrows():
        grpc_comfortband.append(
            temperature_bands_pb2.SchedulePoint(time=int(index.timestamp() * 1e9),
                                        temperature_low=row["t_low"],
                                        temperature_high=row["t_high"],
                                        unit="F"))

    response_creation_time = time.time()
    print("Error checking time %f seconds" % (error_checking_time - start_time ))
    print("Comfortband time %f seconds" % (comfortband_time - error_checking_time ))
    print("Response creation time %f seconds" % (response_creation_time - comfortband_time ))


    return temperature_bands_pb2.ScheduleReply(schedules=grpc_comfortband), None


def get_do_not_exceed(request):
    """Returns preprocessed thermal data for a given request or None."""

    print("received request:", request.building, request.zone, request.start, request.end, request.window, request.unit)
    duration = utils.get_window_in_sec(request.window)

    request_length = [len(request.building), len(request.zone), request.start, request.end,
                      duration]

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    # if request.end > int(time.time() * 1e9):
    #     return None, "invalid request, end date is in the future. Now: %d and end: %d" % (
    #         time.time() * 1e9, request.end)
    if request.start >= request.end:
        return None, "invalid request, start date is after end date."
    if request.start < 0 or request.end < 0:
        return None, "invalid request, negative dates"
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"
    if request.unit != "F":
        return None, "only fahrenheit support."
    if 60*60 % duration != 0:
        return None, "window is not a factor of an hour (60(min)*60(sec)%window != 0). e.g. 15min is a factor but 25 is not."


    start_datetime = datetime.datetime.utcfromtimestamp(
        float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_datetime = datetime.datetime.utcfromtimestamp(
        float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    do_not_exceed, err = get_band(request.building, request.zone, start_datetime, end_datetime, duration, "do_not_exceed")
    if do_not_exceed is None:
        return None, err

    grpc_do_not_exceed = []
    for index, row in do_not_exceed.iterrows():
        grpc_do_not_exceed.append(
            temperature_bands_pb2.SchedulePoint(time=int(index.timestamp() * 1e9),
                                        temperature_low=row["t_low"],
                                        temperature_high=row["t_high"],
                                        unit="F"))

    return temperature_bands_pb2.ScheduleReply(schedules=grpc_do_not_exceed), None


class SchedulesServicer(temperature_bands_pb2_grpc.SchedulesServicer):
    def __init__(self):
        pass

    def GetComfortband(self, request, context):
        """A simple RPC.

        Sends the outside temperature for a given building, within a duration (start, end), and a requested window
        An error  is returned if there are no temperature for the given request
        """

        comfortband, error = get_comfortband(request)
        if comfortband is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return temperature_bands_pb2.ScheduleReply()
        else:
            return comfortband

    def GetDoNotExceed(self, request, context):
        """A simple RPC.

        Sends the outside temperature for a given building, within a duration (start, end), and a requested window
        An error  is returned if there are no temperature for the given request
        """
        do_not_exceed, error = get_do_not_exceed(request)
        if do_not_exceed is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return temperature_bands_pb2.ScheduleReply()
        else:
            return do_not_exceed


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    temperature_bands_pb2_grpc.add_SchedulesServicer_to_server(SchedulesServicer(), server)
    server.add_insecure_port(TEMPERATURE_BANDS_HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()

