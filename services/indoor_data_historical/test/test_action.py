from __future__ import print_function

import grpc
import sys
import pandas as pd
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
import unittest
import xbos_services_getter as xbos
sys.path.append(str(Path.cwd().parent.parent.parent.joinpath("test")))
import test_utils

stub = xbos.get_indoor_historic_stub()
building_zone_names_stub = xbos.get_building_zone_names_stub()
buildings = xbos.get_buildings(building_zone_names_stub)
zones = xbos.get_all_buildings_zones(building_zone_names_stub)

class TestActionData(unittest.TestCase):   
 
    def __init__(self, test_name):
        super(TestActionData, self).__init__(test_name)

    def get_response(self, building="ciee", zone="HVAC_Zone_Eastzone", window="1h", start=-1, end=-1):
        try:
            if start == -1 or end == -1:
                start, end = test_utils.generate_random_time_interval()
            return xbos.get_actions_historic(stub, building=building, zone=zone, start=start,end=end,window=window)
        except grpc.RpcError as e:
            print(e)

    def valid_data_exists(self, response, window):
        last_time = None
        num_items = response.count()
        i = 1
        for time, val in response.iteritems():
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
            time_delta = test_utils.window_to_timedelta(window)
            self.assertEqual(time_diff, time_delta)

        return cur_time
    
    @test_utils.all_buildings_and_zones(max_interval_days=1, log_csv="action_tests.csv", buildings=buildings, zones=zones)
    def all_buildings_and_zones(self, **kwargs):
        response = self.get_response(**kwargs)
        self.assertIsNotNone(response)       
        self.valid_data_exists(response, kwargs.get("window"))
        return response
    
    @test_utils.random_buildings_and_zones(iterations=2, log_csv="action_random_tests.csv", buildings=buildings, zones=zones)
    def test_random_buildings_and_zones(self, **kwargs):
        response = self.get_response(**kwargs)
        self.assertIsNotNone(response)
        self.valid_data_exists(response, kwargs["window"])
        return response

    def random_one_building(self, building='ciee', zone='HVAC_Zone_Northzone', window_unit="h"):
        window = test_utils.generate_random_window(window_unit)
        start, end = test_utils.generate_random_time_interval()
        response = self.get_response(building=building, zone=zone, window=window, start=start, end=end)
        self.assertIsNotNone(response)
        self.valid_data_exists(response, window)

if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestActionData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestActionData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
