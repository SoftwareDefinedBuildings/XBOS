from concurrent import futures
import time
import grpc
import logging
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.DEBUG)
import occupancy_pb2
import occupancy_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

import os
import xbos_services_utils3 as utils
import datetime
import pytz
import numpy as np
import pandas as pd
import yaml

DAYS_IN_WEEK = 7
OCCUPANCY_DATA_PATH = os.environ["OCCUPANCY_DATA_PATH"]
OCCUPANCY_HOST_ADDRESS = os.environ["OCCUPANCY_HOST_ADDRESS"]

def _get_occupancy_config(building, zone):
    occ_path = OCCUPANCY_DATA_PATH + "/" + building + "/" + zone + ".yml"

    if os.path.exists(occ_path):
        with open(occ_path, "r") as f:
            try:
                config = yaml.load(f)
            except yaml.YAMLError:
                return None, "yaml could not read file at: %s" % occ_path
    else:
        return None, "occupancy file could not be found. path: %s." % occ_path

    return config, None


def _get_week_occupancy(building, zone, date, interval):
    """
    Gets the occupancy from the zone configuration file. Correctly Resamples the data according to interval
    :param date: The date for which we want to start the week. Timezone aware.
    :param interval: int:seconds. The interval/frequency of resampling.
    :return: pd.Series with time_series index in timezone of building.
    """
    config, err = _get_occupancy_config(building, zone)
    if config is None:
        return None, err

    # Set the date to the controller timezone.
    building_date = date.astimezone(tz=pytz.timezone(config["tz"]))
    weekday = building_date.weekday()

    list_occ_data = []

    occ_data = config["occupancy"]

    # Note, we need to get a day before the start and after the end of the week to correctly resample due to timezones.
    for i in range(DAYS_IN_WEEK + 2):
        curr_weekday = (weekday + i - 1) % DAYS_IN_WEEK
        curr_day = building_date + datetime.timedelta(days=i - 1)

        curr_idx = []
        curr_occ = []

        date_occupancy = np.array(occ_data[curr_weekday])

        for interval_occupancy in date_occupancy:
            start, end, occ = interval_occupancy
            start = utils.combine_date_time(start, curr_day)

            occ = float(occ)
            curr_idx.append(start)
            curr_occ.append(occ)

        list_occ_data.append(pd.Series(index=curr_idx, data=curr_occ))

    series_occ = pd.concat(list_occ_data)

    series_occ = series_occ.tz_convert(date.tzinfo)

    # decrements in interval-steps till beginning of day of date.
    decremented_date = utils.decrement_to_start_of_day(date, interval)

    series_occ = utils.smart_resample(series_occ, decremented_date, decremented_date + datetime.timedelta(days=7),
                                      interval, "pad")

    return series_occ, None


def get_all_occ(building, zone, start, end, interval):
    """
    Gets the occupancy of a zone from start to end in the given interval.
    :param building: string
    :param zone: string
    :param start: datetime. timezone aware
    :param end: datetime. timezone aware.
    :param interval: int:seconds. seconds_in_day % interval == 0
    :return:

    NOTE: If (end-start).total_seconds % interval != 0, then make new_end such that new_end < end and
    the condition is satisfied. New_end will also not be inclusive.
    """

    first_seven_days, err = _get_week_occupancy(building, zone, start, interval)
    if first_seven_days is None:
        return None, err

    first_seven_days_start = first_seven_days.index[0]
    first_seven_days_end = first_seven_days_start + datetime.timedelta(days=DAYS_IN_WEEK)

    if end < first_seven_days_end:
        return first_seven_days[start:end][:-1], None

    # get occupancy for the remaining days.
    remaining_data = []

    for i in range((end - first_seven_days_end).days + 1):
        curr_offset = i % DAYS_IN_WEEK

        curr_time = first_seven_days_end + datetime.timedelta(days=i)

        curr_data = first_seven_days[first_seven_days_start + datetime.timedelta(days=curr_offset):
                                     first_seven_days_start + datetime.timedelta(days=curr_offset + 1)][
                    :int(24 * 60 * 60 / interval)]

        curr_start_date = curr_time
        curr_end_date = curr_start_date + datetime.timedelta(days=1)
        date_range = pd.date_range(start=curr_start_date, end=curr_end_date, freq=str(interval) + "S")[:-1]
        curr_data.index = date_range

        remaining_data.append(curr_data)

    occupancy_series = pd.concat([first_seven_days] + remaining_data)

    return occupancy_series[start:end][:-1], None


def get_occupancy(request):
    """Returns preprocessed thermal data for a given request or None."""
    logging.info("received request:", request.building, request.zone, request.start, request.end, request.window)
    window_seconds = utils.get_window_in_sec(request.window)

    request_length = [len(request.building), len(request.zone), request.start, request.end,
                      window_seconds]

    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if request.start >= request.end:
        return None, "invalid request, start date is after end date."
    if request.start < 0 or request.end < 0:
        return None, "invalid request, negative dates"
    if request.start + (window_seconds * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"
    if 60 * 60 % window_seconds != 0:
        return None, "window does not evenly divide a day (seconds_in_day % window != 0)."

    start_datetime = datetime.datetime.utcfromtimestamp(
        float(request.start / 1e9)).replace(tzinfo=pytz.utc)
    end_datetime = datetime.datetime.utcfromtimestamp(
        float(request.end / 1e9)).replace(tzinfo=pytz.utc)

    all_occupancy, err = get_all_occ(request.building, request.zone, start_datetime, end_datetime, window_seconds)
    if all_occupancy is None:
        return None, err

    grpc_occ = []
    for idx, row in all_occupancy.iteritems():
        grpc_occ.append(
            occupancy_pb2.OccupancyPoint(time=int(idx.timestamp() * 1e9), occupancy=row))

    return occupancy_pb2.OccupancyReply(occupancies=grpc_occ), None


class OccupancyServicer(occupancy_pb2_grpc.OccupancyServicer):
    def __init__(self):
        pass

    def GetOccupancy(self, request, context):
        """A simple RPC.

        Sends the outside temperature for a given building, within a duration (start, end), and a requested window
        An error  is returned if there are no temperature for the given request
        """
        occupancy, error = get_occupancy(request)
        if occupancy is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return occupancy_pb2.OccupancyReply()
        else:
            return occupancy


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    occupancy_pb2_grpc.add_OccupancyServicer_to_server(OccupancyServicer(), server)
    server.add_insecure_port(OCCUPANCY_HOST_ADDRESS)
    logging.info("Serving on {0} with data path {1}".format(OCCUPANCY_HOST_ADDRESS, OCCUPANCY_DATA_PATH))
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
