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
import os
print(Path.parent)
sys.path.append(str(Path.parent))
from test_helper import TestHelper

class TestOccupancyData(TestHelper):   

    def __init__(self, test_name):
        TestHelper.__init__(self, test_name)
        self.stub = xbos.get_occupancy_stub()
        self.yaml_file_name = "no_occupancy_data.yml"

    def get_response(self, building="ciee", zone="HVAC_Zone_Eastzone", window="1h", start=-1, end=-1):
        try:
            if start == -1 or end == -1:
                end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
                start = end - datetime.timedelta(days=10)
                # alternate start and end times below
                # start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
                # end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            return xbos.get_occupancy(self.stub, building=building, zone=zone, start=start,end=end,window=window)
        except grpc.RpcError as e:
            print(e)
            
if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestOccupancyData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestOccupancyData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
