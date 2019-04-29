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

stub = xbos.get_price_stub()
building_zone_names_stub = xbos.get_building_zone_names_stub()
buildings = xbos.get_buildings(building_zone_names_stub)
class TestTariffUtilityData(unittest.TestCase):   

    def __init__(self, test_name):
        super(TestTariffUtilityData, self).__init__(test_name)

    def get_response(self, building="ciee"):
        try:
            return xbos.get_tariff_and_utility(stub, building=building)
        except grpc.RpcError as e:
            print(e)
    
    def valid_data_exists(self, response):
        self.assertIsInstance(response, cls=dict)
        self.assertIsNotNone(response["utility"])
        self.assertIsNotNone(response["tariff"])
        self.assertIsInstance(response["utility"], cls=str)
        self.assertIsInstance(response["tariff"], cls=str)
    
    @test_utils.only_by_building(log_csv="tariff_utility_tests.csv", buildings=buildings)
    def test_all_buildings_and_zones(self, **kwargs):
        response = self.get_response(**kwargs)
        self.assertIsNotNone(response)
        self.valid_data_exists(response)
        return response
                    
if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestTariffUtilityData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestTariffUtilityData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
