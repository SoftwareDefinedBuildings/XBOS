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

class TestTariffUtilityData(TestHelper):   

    def __init__(self, test_name):
        TestHelper.__init__(self, test_name)
        self.stub = xbos.get_price_stub()
        self.yaml_file_name = "no_tariff_utility_data.yml"

    def get_response(self, building="ciee"):
        try:
            return xbos.get_tariff_and_utility(self.stub, building=building)
        except grpc.RpcError as e:
            print(e)
    
    def valid_data_exists(self, response):
        self.assertIsInstance(response, cls=dict)
        self.assertIsNotNone(response["utility"])
        self.assertIsNotNone(response["tariff"])
        self.assertIsInstance(response["utility"], cls=str)
        self.assertIsInstance(response["tariff"], cls=str)
    
    def test_all_buildings_and_zones(self):
        no_data = []
        for building in self.buildings:
            response = self.get_response(building=building)
            if response is None:
                if building not in no_data:
                    no_data.append(building)
            else:
                print(building)
                self.response_exists(response)
                self.valid_data_exists(response)
        
        self.generate_yaml_file(self.yaml_file_name, no_data)
            
if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestTariffUtilityData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestTariffUtilityData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
