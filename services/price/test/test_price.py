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

class TestPriceData(TestHelper):   

    def __init__(self, test_name):
        TestHelper.__init__(self, test_name)
        self.stub = xbos.get_price_stub()
        self.yaml_file_name = "no_price_data.yml"

    def get_response(self, building="ciee", price_type="ENERGY", window="1h", start=-1, end=-1):
        try:
            if start == -1 or end == -1:
                end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
                start = end - datetime.timedelta(days=10)
                # alternate start and end times below
                # start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
                # end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            return xbos.get_price(self.stub, building=building, price_type=price_type, start=start,end=end,window=window)
        except grpc.RpcError as e:
            print(e)
    
    def valid_data_exists(self, response, window):
        last_time = None
        num_items = response.count()
        i = 1
        for time, row in response.iterrows():
            if i < num_items - 1:
                self.assertIsNone(row)
                self.assertIsNotNone(row['price'])
                self.assertIsNotNone(row['unit'])
                self.assertIsNotNone(time)
                self.assertIsInstance(obj=time, cls=pd.Timestamp)
                self.assertIsInstance(obj=row['price'], cls=float)
                self.assertIsInstance(obj=row['unit'], cls=str)
                last_time = self.window_is_accurate(last_time, time.to_pydatetime(), window)
            i += 1
    
    def test_all_buildings_and_zones(self):
        response = self.get_response()

        print(response)
        # no_data = []
        # window = "1h"
        # for building in self.buildings:
        #     response = self.get_response(building=building, price_type="ENERGY", window=window)
        #     if response is None:
        #         if building not in no_data:
        #             no_data.append(building)
        #     else:
        #         print(building)
        #         self.response_exists(response)
        #         self.valid_data_exists(response, window)
            
        #     response = self.get_response(building=building, price_type="DEMAND", window=window)
        #     if response is None:
        #         if building not in no_data:
        #             no_data.append(building)
        #     else:
        #         print(building)
        #         self.response_exists(response)
        #         self.valid_data_exists(response, window)
        
        # self.generate_yaml_file(self.yaml_file_name, no_data)
            
if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestPriceData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestPriceData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
