from __future__ import print_function

import grpc
import time
import datetime
import calendar
import pytz
import sys
import yaml
import math
import pandas as pd
from pathlib import Path
import numpy as np
sys.path.append(str(Path.cwd().parent))
import unittest
import xbos_services_getter as xbos

class TestHelper(unittest.TestCase):   

    def __init__(self, test_name):
        super(TestHelper, self).__init__(test_name)
        self.stub = xbos.get_indoor_historic_stub() #Default
        building_zone_names_stub = xbos.get_building_zone_names_stub()
        self.buildings = xbos.get_buildings(building_zone_names_stub)
        self.zones = xbos.get_all_buildings_zones(building_zone_names_stub)
        self.window = "1h"
        self.yaml_file_name = "no-data.yml"

    def get_response(self, building="ciee", zone="HVAC_Zone_Eastzone", window="1h", start=-1, end=-1):
        try:
            if start == -1 or end == -1:
                end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
                start = end - datetime.timedelta(days=10)
                # alternate start and end times below
                # start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
                # end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            return xbos.get_indoor_temperature_historic(self.stub, building=building, zone=zone, start=start,end=end,window=window)
        except grpc.RpcError as e:
            print(e)
    
    def response_exists(self, response):
        self.assertIsNotNone(response)       
    
    def valid_data_exists(self, response, window):
        last_time = None
        num_items = response.shape[0]
        i = 1
        for time, val in response.iterrows():
            if i < num_items - 1:
                self.assertIsNotNone(val)
                self.assertIsNotNone(time)
                self.assertIsInstance(obj=time, cls=pd.Timestamp)
                self.assertIsInstance(obj=val, cls=float)
                last_time = self.window_is_accurate(last_time, time.to_pydatetime(), window)
            i += 1
    
    def window_is_accurate(self, last_time, cur_time, window):
        if last_time is not None:
            time_diff = cur_time - last_time
            time_delta = self.window_to_timedelta(window)
            self.assertEqual(time_diff, time_delta)

        return cur_time
    
    def window_to_timedelta(self, window):
        unit = window[-1]
        time = float(window[:-1])

        units = {
            "h": datetime.timedelta(hours=time),
            "m": datetime.timedelta(minutes=time),
            "s": datetime.timedelta(seconds=time),
            "d": datetime.timedelta(days=time),
            "w": datetime.timedelta(weeks=time),
            "y": datetime.timedelta(weeks=time*52)
        }

        return units[unit]
        
    def all_buildings_test(self):
        no_data = {}
        for building in self.buildings:
            for zone in self.zones[building]:
                response = self.get_response(building=building, zone=zone, window=self.window)

                if response is None:
                    if building in no_data:
                        no_data[building].append(zone)
                    else:
                        no_data[building] = [zone]
                else:
                    print(building, zone)
                    self.response_exists(response)
                    self.valid_data_exists(response, self.window)

        self.generate_yaml_file(self.yaml_file_name, no_data)

    def random_test_all_buildings(self, num_iterations=1):
        
        for i in range(num_iterations):
            window = "1h"#self.generate_random_window('h')
            start, end = self.generate_random_time_interval()
            no_data = { window: window, start: start, end: end }
            for building in self.buildings:
                for zone in self.zones[building]:
                    response = self.get_response(building=building, zone=zone, window=window, start=start, end=end)

                    if response is None:
                        if building in no_data:
                            no_data[building].append(zone)
                        else:
                            no_data[building] = [zone]
                    else:
                        print(building, zone)
                        self.response_exists(response)
                        self.valid_data_exists(response, window)

            self.generate_yaml_file("failed_tests/" + self.yaml_file_name + str(i + 1) + ".yml", no_data)
        
    def random_test_single_building(self, building='ciee', zone='HVAC_Zone_Northzone', window_unit="h"):
        window = self.generate_random_window(window_unit)
        start, end = self.generate_random_time_interval()
        response = self.get_response(building=building, zone=zone, window=window, start=start, end=end)
        self.response_exists(response)
        self.valid_data_exists(response, window)

    def generate_yaml_file(self, file_path, data):
        with open(file_path, 'w') as outfile:
            yaml.dump(data, outfile)
    
    def generate_random_time_interval(self):
        """ Generates a time interval between 3 years ago and now """
        num_years_ago = np.float32(self.random_float(0.5, 3)).item()
        end = datetime.datetime.now().replace(tzinfo=pytz.utc)
        start = end - datetime.timedelta(weeks=52 * num_years_ago)
        end = start + datetime.timedelta(minutes=np.uint32(self.random_int(10, int((end - start).total_seconds() / 60))).item())
        
        return start, end

    def generate_random_window(self, unit="h"):
        units = {
            "h": self.random_int(1, 24),
            "m": self.random_int(1, 60),
            "s": self.random_int(30, 3600),
            "d": self.random_int(1, 30),
            "w": self.random_int(1, 20),
            "y": self.random_int(1, 3)
        }

        return str(units[unit]) + unit

    def random_float(self, minimum, maximum):
        """ Minimum and maximum are inclusive """
        return np.random.uniform(minimum, maximum)

    def random_int(self, minimum, maximum):
        """ Minimum and maximum are inclusive """
        return np.random.randint(low=minimum, high=maximum + 1, size=1)[0]



