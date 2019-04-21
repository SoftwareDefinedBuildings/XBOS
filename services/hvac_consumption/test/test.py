from __future__ import print_function

import grpc
import sys
import datetime
import pytz
import pandas as pd
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
import unittest
import xbos_services_getter as xbos
sys.path.append(str(Path.cwd().parent.parent.parent.joinpath("test")))
import test_utils

stub = xbos.get_hvac_consumption_stub()
building_zone_names_stub = xbos.get_building_zone_names_stub()
buildings = xbos.get_buildings(building_zone_names_stub)
zones = xbos.get_all_buildings_zones(building_zone_names_stub)
class TestHVACConsumptionData(unittest.TestCase):   
 
    def __init__(self, test_name):
        super(TestHVACConsumptionData, self).__init__(test_name)

    def get_response(self, building="ciee", zone="HVAC_Zone_Eastzone"):
        try:
            return xbos.get_hvac_consumption(stub, building=building, zone=zone)
        except grpc.RpcError as e:
            print(e)
    
    def valid_data_exists(self, response):
        self.assertIsInstance(response, cls=dict)
        for key in response:
            self.assertIsNotNone(key)
            self.assertIsNotNone(response[key])
            self.assertIsInstance(obj=key, cls=int)
            self.assertTrue(type(response[key]) == int or type(response[key]) == float)
    
    @test_utils.only_by_building_and_zone(log_csv="hvac_consumption_tests.csv", buildings=buildings, zones=zones)
    def test_all_buildings_and_zones(self, **kwargs):
        response = self.get_response(**kwargs)
        self.assertIsNotNone(response)
        self.valid_data_exists(response)
        return response
                

if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestHVACConsumptionData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestHVACConsumptionData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
