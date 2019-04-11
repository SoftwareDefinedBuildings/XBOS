from __future__ import print_function

import grpc
import time
import datetime
import calendar
import pytz
import sys
import pandas as pd
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
import unittest
import xbos_services_getter as xbos
from test_helper import TestHelper

class TestHVACConsumptionData(TestHelper):   
 
    def __init__(self, test_name):
        TestHelper.__init__(self, test_name)
        self.stub = xbos.get_hvac_consumption_stub()
        self.yaml_file_name = "no_hvac_consumption_data.yml"

    def get_response(self, building="ciee", zone="HVAC_Zone_Eastzone"):
        try:
            return xbos.get_hvac_consumption(self.stub, building=building, zone=zone)
        except grpc.RpcError as e:
            print(e)
    
    def valid_data_exists(self, response):
        self.assertIsInstance(response, cls=dict)
        for key in response:
            self.assertIsNotNone(key)
            self.assertIsNotNone(response[key])
            self.assertIsInstance(obj=key, cls=int)
            self.assertTrue(type(response[key]) == int or type(response[key]) == float)
    
    def test_all_buildings_and_zones(self):
        no_data = {}
        for building in self.buildings:
            for zone in self.zones[building]:
                response = self.get_response(building=building, zone=zone)

                if response is None:
                    if building in no_data:
                        no_data[building].append(zone)
                    else:
                        no_data[building] = [zone]
                else:
                    print(building, zone)
                    self.response_exists(response)
                    self.valid_data_exists(response)

if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestHVACConsumptionData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestHVACConsumptionData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
