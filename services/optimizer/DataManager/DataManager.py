import time

import datetime
import pytz
import pandas as pd
import numpy as np

import xbos_services_getter as xsg


def check_data_zones(zones, data_dict, start, end, window):
    for zone in zones:
        if zone not in data_dict:
            return "Is missing zone " + zone
        err = xsg.check_data(data_dict[zone], start, end, window, check_nan=True)
        if err is not None:
            return err
    return None


"""Allows to easily retrieve all necessary data for doing Optimizations and Simulations.
Will get all data which is not found in the non_controallable_data argument."""
class DataManager:
    def __init__(self, building, zones, start, end, window, non_controllable_data={}):
        """Exposes:
            - self.comfortband
            - self.do_not_exceed
            - self.occupancy
            - self.outdoor_temperature
            - self.discomfort_stub
            - self.hvac_consumption

            - self.start
            - self.unix_start
            - self.end
            - self.unix_end
            - self.window

            - self.building
            - self.zones


        :param building:
        :param zones:
        :param start:
        :param end:
        :param window:
        :param non_controllable_data: possible keys:
                ["comfortband", "do_not_exceed", "occupancy", "outdoor_temperature"]
                for each key the value needs to be a dictionary with {zone: data} for all zones in self.zones.
                Outdoor temperature is just data since it is data for the whole building.
        """

        self.start = start
        self.unix_start = start.timestamp() * 1e9
        self.end = end
        self.unix_end = end.timestamp() * 1e9
        self.window = window  # timedelta string

        self.building = building
        self.zones = zones

        if non_controllable_data is None:
            non_controllable_data = {}
        # TODO add error checking. check that the right zones are given in non_controllable_data and that the start/end/window are right.

        # Documentation: All data here is in timeseries starting exactly at start and every step corresponds to one
        # interval. The end is not inclusive.

        # temperature band
        temperature_band_stub = xsg.get_temperature_band_stub()

        if "comfortband" not in non_controllable_data:
            self.comfortband = {
            iter_zone: xsg.get_comfortband(temperature_band_stub, self.building, iter_zone, self.start, self.end,
                                           self.window)
            for iter_zone in self.zones}
        else:
            self.comfortband = non_controllable_data["comfortband"]
        err = check_data_zones(self.zones, self.comfortband, start, end, window)
        if err is not None:
            raise Exception("Bad comfortband given. " + err)

        if "do_not_exceed" not in non_controllable_data:
            self.do_not_exceed = {
            iter_zone: xsg.get_do_not_exceed(temperature_band_stub, self.building, iter_zone, self.start, self.end,
                                             self.window)
            for iter_zone in self.zones}
        else:
            self.do_not_exceed = non_controllable_data["do_not_exceed"]
        err = check_data_zones(self.zones, self.do_not_exceed, start, end, window)
        if err is not None:
            raise Exception("Bad DoNotExceed given. " + err)

        # occupancy
        if "occupancy" not in non_controllable_data:
            occupancy_stub = xsg.get_occupancy_stub()
            self.occupancy = {
            iter_zone: xsg.get_occupancy(occupancy_stub, self.building, iter_zone, self.start, self.end, self.window)
            for iter_zone in self.zones}
        else:
            self.occupancy = non_controllable_data["occupancy"]
        err = check_data_zones(self.zones, self.occupancy, start, end, window)
        if err is not None:
            raise Exception("Bad occupancy given. " + err)

        # outdoor temperatures
        if "outdoor_temperature" not in non_controllable_data:
            outdoor_historic_stub = xsg.get_outdoor_historic_stub()
            self.outdoor_temperature = xsg.get_outdoor_temperature_historic(outdoor_historic_stub, self.building,
                                                                            self.start, self.end, self.window)
        else:
            self.outdoor_temperature = non_controllable_data["outdoor_temperature"]
        err = xsg.check_data(self.outdoor_temperature, start, end, window, check_nan=True)
        if err is not None:
            raise Exception("Bad outdoor temperature given. " + err)
        #         outdoor_prediction_channel = grpc.insecure_channel(OUTSIDE_PREDICTION)
        #         outdoor_prediction_stub = outdoor_temperature_prediction_pb2_grpc.OutdoorTemperatureStub(outdoor_prediction_channel)

        #         self.outdoor_temperatures = get_outside_temperature(
        #             outdoor_historic_stub, outdoor_prediction_stub, self.building, self.start, self.end, self.window)

        # discomfort channel
        self.discomfort_stub = xsg.get_discomfort_stub()

        # HVAC Consumption TODO ERROR CHECK?
        hvac_consumption_stub = xsg.get_hvac_consumption_stub()
        self.hvac_consumption = {iter_zone: xsg.get_hvac_consumption(hvac_consumption_stub, building, iter_zone)
                                 for iter_zone in self.zones}

        # TODO Prices

