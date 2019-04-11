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
import signal
sys.path.append(str(Path.cwd().parent))
import price_pb2
import price_pb2_grpc
import unittest
import xbos_services_getter as xbos
from test_helper import TestHelper
import os

# def run():
#     # NOTE(gRPC Python Team): .close() is possible on a channel and should be
#     # used in circumstances in which the with statement does not fit the needs
#     # of the code.
#     with grpc.insecure_channel('localhost:50060') as channel:
#         stub = price_pb2_grpc.PriceStub(channel)
#         try:
#             # response = stub.GetPrice(price_pb2.PriceRequest(utility="PGE",tariff="PGEA10",price_type="energy",start=int((time.time())*1000000000.0),end=int((time.time()+3600*2)*1000000000.0),window="15m"))
#             # start = int(time.mktime(datetime.datetime.strptime("2/02/2019 2:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
#             # end =  int(time.mktime(datetime.datetime.strptime("2/02/2019 22:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)

#             #----------------------
#             end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
#             start = end - datetime.timedelta(days=10)
#             start = int(time.mktime(start.timetuple())*1e9)
#             end =  int(time.mktime(end.timetuple())*1e9)

#             tariff_and_utility = stub.GetTariffAndUtility(price_pb2.BuildingRequest(building="ciee"))
#             response = stub.GetPrice(price_pb2.PriceRequest(price_type="ENERGY", tariff=tariff_and_utility.tariff, utility=tariff_and_utility.utility, start=start,end=end,window="1h"))
#             print(response)
#             # for temperature in response.temperatures:
#             #     # print("Price at: %s is: %.2f %s" % (time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(int(price.time/1000000000.0))) + ' UTC', price.price, price.unit))
#             #     print("Temp at: %s is: %.2f %s" % (time.ctime(int(temperature.time/1e9)) + ' PST', temperature.temperature, temperature.unit))
#         except grpc.RpcError as e:
#             print(e)


# if __name__ == '__main__':
#      run()

class TestPriceData(TestHelper):   

    def __init__(self, test_name):
        TestHelper.__init__(self, test_name)
        self.stub = xbos.get_price_stub()
        self.yaml_file_name = "no_price_data"

    def get_response(self, building="ciee", price_type="ENERGY", window="1h", start=-1, end=-1):
        
        def handler(signum, frame):
            raise Exception("No data received")

        #signal.signal(signal.SIGALRM, handler)

        try:
            if start == -1 or end == -1:
                # end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
                # start = end - datetime.timedelta(days=10)
                start = datetime.datetime.strptime("09/09/2018 07:00:00", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
                end =  datetime.datetime.strptime("31/12/2018 23:59:59", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
                # end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
                # start = end - datetime.timedelta(days=10)
                # alternate start and end times below
                # start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
                # end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)

            #signal.alarm(10)
            return xbos.get_price(self.stub, building=building, price_type=price_type, start=start,end=end,window=window)
        except grpc.RpcError as e:
            print(e)
    
    def valid_data_exists(self, response, window):
        last_time = None
        num_rows = response.shape[0]
        i = 1
        #num_zeros = 0
        for time, row in response.iterrows():
            if i < num_rows - 3:
                self.assertIsNotNone(row)
                self.assertIsNotNone(row['price'])
                self.assertIsNotNone(row['unit'])
                self.assertIsNotNone(time)
                self.assertIsInstance(obj=time, cls=pd.Timestamp)
                self.assertIsInstance(obj=row['price'], cls=float)
                # if row['price'] == 0:
                #     num_zeros += 1
                # print(row['price'], row['unit'])
                # if math.isnan(row['price']):
                #     num_nans += 1
                self.assertTrue(type(row['unit']) == float or type(row['unit']) == str)
                last_time = self.window_is_accurate(last_time, time.to_pydatetime(), window)
            i += 1
        
        #print("Zeros", num_zeros)
        
    def tes_all_buildings(self):
        #self.all_buildings_test()
        return 5
        
    def all_buildings_test(self):        
        window = "1h"
        no_energy_data = { "window": window, "buildings": [] }
        no_demand_data = { "window": window, "buildings": [] }
        for building in self.buildings:
            response = self.get_response(building=building, price_type="ENERGY", window=window)
            if response is None:
                if building not in no_energy_data['buildings']:
                    no_energy_data['buildings'].append(building)
            else:
                print(building, "ENERGY")
                self.response_exists(response)
                self.valid_data_exists(response, window)
        
            response = self.get_response(building=building, price_type="DEMAND", window=window)
            if response is None:
                if building not in no_demand_data['buildings']:
                    no_demand_data['buildings'].append(building)
            else:
                print(building, "DEMAND")
                self.response_exists(response)
                self.valid_data_exists(response, window)
            
        self.generate_yaml_file("no_price_energy_data.yml", no_energy_data)
        self.generate_yaml_file("no_price_demand_data.yml", no_demand_data)
    
    def test_random_all_buildings(self):
        self.random_test_all_buildings(num_iterations=2)
    
    def random_test_all_buildings(self, num_iterations=1):

        for i in range(num_iterations):
            window = self.generate_random_window(unit='m', minimum=40)
            start = datetime.datetime.strptime("09/09/2018 07:00:00", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
            end =  datetime.datetime.strptime("31/12/2018 23:59:59", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
            start, end = self.generate_random_time_interval(start=start, end=end, max_interval_days=2)
            print("START", start)
            print("END", end)
            print("WINDOW", window)
            no_energy_data = { "window": window, "start": start, "end": end, "buildings":[] }
            no_demand_data = { "window": window, "start": start, "end": end, "buildings":[] }
            for building in self.buildings:
                response = self.get_response(building=building, price_type="ENERGY", window=window, start=start, end=end)
                if response is None:
                    if building not in no_energy_data['buildings']:
                        no_energy_data['buildings'].append(building)
                else:
                    print(building, "ENERGY")
                    self.response_exists(response)
                    self.valid_data_exists(response, window)

                response = self.get_response(building=building, price_type="DEMAND", window=window, start=start, end=end)
                if response is None:
                    if building not in no_demand_data['buildings']:
                        no_demand_data['buildings'].append(building)
                else:
                    print(building, "DEMAND")
                    self.response_exists(response)
                    self.valid_data_exists(response, window)

            self.generate_yaml_file("failed_tests/no_price_energy_data" + str(i + 1) + ".yml", no_energy_data)
            self.generate_yaml_file("failed_tests/no_price_demand_data" + str(i + 1) + ".yml", no_demand_data)
        
    
if __name__ == '__main__':
    test_loader = unittest.TestLoader()
    test_names = test_loader.getTestCaseNames(TestPriceData)

    suite = unittest.TestSuite()
    for test_name in test_names:
        suite.addTest(TestPriceData(test_name))

    result = unittest.TextTestRunner().run(suite)

    sys.exit(not result.wasSuccessful())
