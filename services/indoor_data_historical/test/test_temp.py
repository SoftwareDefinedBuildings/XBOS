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
sys.path.append(str(Path.cwd().parent))
import unittest
import xbos_services_getter as xbos

class TestTemperatureData(unittest.TestCase):   

    def __init__(self, test_name):
        super(TestTemperatureData, self).__init__(test_name)
        self.stub = xbos.get_indoor_historic_stub()
        building_zone_names_stub = xbos.get_building_zone_names_stub()
        self.buildings = xbos.get_buildings(building_zone_names_stub)
        self.zones = xbos.get_all_buildings_zones(building_zone_names_stub)

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
        num_items = response.count()
        i = 1
        for time, temp in response.iteritems():
            if i < num_items - 1:
                self.assertIsNotNone(temp)
                self.assertIsNotNone(time)
                self.assertIsInstance(obj=time, cls=pd.Timestamp)
                self.assertIsInstance(obj=temp, cls=float)
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

        if unit == 'h':
            return datetime.timedelta(hours=time)
        elif unit == 'm':
            return datetime.timedelta(minutes=time)
        elif unit == 's':
            return datetime.timedelta(seconds=time)
        elif unit == 'd':
            return datetime.timedelta(days=time)
        elif unit == 'y':
            return datetime.timedelta(weeks=time*52)
        elif unit == 'w':
            return datetime.timedelta(weeks=time)
        
    def test_all_buildings_and_zones(self):
        no_data = {}
        window = "1h"
        for building in self.buildings:
            for zone in self.zones[building]:
                response = self.get_response(building=building, zone=zone, window=window)

                if response is None:
                    if building in no_data:
                        no_data[building].append(zone)
                    else:
                        no_data[building] = [zone]
                else:
                    print(building, zone)
                    self.response_exists(response)
                    self.valid_data_exists(response, window)
        
        with open('no_temp_data.yml', 'w') as outfile:
            yaml.dump(no_data, outfile)
            
if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestTemperatureData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestTemperatureData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
