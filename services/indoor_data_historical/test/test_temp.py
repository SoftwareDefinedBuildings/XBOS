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
from test_helper import TestHelper

class TestTemperatureData(TestHelper):   

    def __init__(self, test_name):
        TestHelper.__init__(self, test_name)
        self.stub = xbos.get_indoor_historic_stub()
        self.yaml_file_name = "no_temp_data.yml"

    def get_response(self, building="ciee", zone="HVAC_Zone_Eastzone", window="1h", start=-1, end=-1):
        try:
            if start == -1 or end == -1:
                start, end = self.generate_random_time_interval()
                # end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
                # start = end - datetime.timedelta(days=10)
                # alternate start and end times below
                # start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
                # end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            return xbos.get_indoor_temperature_historic(self.stub, building=building, zone=zone, start=start,end=end,window=window)
        except grpc.RpcError as e:
            print(e)
    
    def test_all_buildings(self):
        self.all_buildings_test()

    def test_random_all_buildings(self):
        self.random_test_all_buildings(num_iterations=2)
            
if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestTemperatureData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestTemperatureData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
