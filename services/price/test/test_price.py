from __future__ import print_function

import grpc
import sys
import datetime
import time
import pytz
import pandas as pd
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
import price_pb2
import price_pb2_grpc
import unittest
import xbos_services_getter as xbos
sys.path.append(str(Path.cwd().parent.parent.parent.joinpath("test")))
import test_utils

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50000') as channel:
        stub = price_pb2_grpc.PriceStub(channel)
        try:
            # response = stub.GetPrice(price_pb2.PriceRequest(utility="PGE",tariff="PGEA10",price_type="energy",start=int((time.time())*1000000000.0),end=int((time.time()+3600*2)*1000000000.0),window="15m"))
            # start = int(time.mktime(datetime.datetime.strptime("09/09/2018 07:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            # end =  int(time.mktime(datetime.datetime.strptime("31/12/2018 23:59:59", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)

            start = int(time.mktime(datetime.datetime.strptime("18/04/2019 01:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            end =  int(time.mktime(datetime.datetime.strptime("20/04/2019 23:59:59", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            #----------------------
            # end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
            # start = end - datetime.timedelta(days=10)
            # start = int(time.mktime(start.timetuple())*1e9)
            # end =  int(time.mktime(end.timetuple())*1e9)


            tariff_and_utility = stub.GetTariffAndUtility(price_pb2.BuildingRequest(building="ciee"))
            response = stub.GetPrice(price_pb2.PriceRequest(price_type="ENERGY", tariff=tariff_and_utility.tariff, utility=tariff_and_utility.utility, start=start,end=end,window="1h"))
            for resp in response:
                print(resp)
            # for temperature in response.temperatures:
            #     # print("Price at: %s is: %.2f %s" % (time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(int(price.time/1000000000.0))) + ' UTC', price.price, price.unit))
            #     print("Temp at: %s is: %.2f %s" % (time.ctime(int(temperature.time/1e9)) + ' PST', temperature.temperature, temperature.unit))
        except grpc.RpcError as e:
            print(e)


if __name__ == '__main__':
     run()
# stub = xbos.get_price_stub()
# building_zone_names_stub = xbos.get_building_zone_names_stub()
# buildings = xbos.get_buildings(building_zone_names_stub)
# zones = xbos.get_all_buildings_zones(building_zone_names_stub)
# start = datetime.datetime.strptime("09/09/2018 07:00:00", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
# end =  datetime.datetime.strptime("31/12/2018 23:59:59", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
# class TestPriceData(unittest.TestCase):

#     def __init__(self, test_name):
#         super(TestPriceData, self).__init__(test_name)

#     def get_response(self, building="ciee", price_type="ENERGY", window="1h", start=-1, end=-1):
#         try:
#             if start == -1 or end == -1:
#                 # end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
#                 # start = end - datetime.timedelta(days=10)
#                 start = datetime.datetime.strptime("09/09/2018 07:00:00", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
#                 end =  datetime.datetime.strptime("31/12/2018 23:59:59", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)

#             return xbos.get_price(stub, building=building, price_type=price_type, start=start,end=end,window=window)
#         except grpc.RpcError as e:
#             print(e)

#     def window_is_accurate(self, last_time, cur_time, window):
#         if last_time is not None:
#             time_diff = cur_time - last_time
#             time_delta = test_utils.window_to_timedelta(window)
#             self.assertEqual(time_diff, time_delta)

#         return cur_time

#     def valid_data_exists(self, response, window):
#         last_time = None
#         num_rows = response.shape[0]
#         i = 1
#         #num_zeros = 0
#         for time, row in response.iterrows():
#             if i < num_rows - 3:
#                 self.assertIsNotNone(row)
#                 self.assertIsNotNone(row['price'])
#                 self.assertIsNotNone(row['unit'])
#                 self.assertIsNotNone(time)
#                 self.assertIsInstance(obj=time, cls=pd.Timestamp)
#                 self.assertIsInstance(obj=row['price'], cls=float)
#                 # if row['price'] == 0:
#                 #     num_zeros += 1
#                 # print(row['price'], row['unit'])
#                 # if math.isnan(row['price']):
#                 #     num_nans += 1
#                 self.assertTrue(type(row['unit']) == float or type(row['unit']) == str)
#                 last_time = self.window_is_accurate(last_time, time.to_pydatetime(), window)
#             i += 1

#     @test_utils.all_buildings(start=start, end=end, max_interval_days=1, log_csv="price_energy_tests.csv", buildings=buildings, price_type="ENERGY")
#     def test_all_buildings(self, **kwargs):
#         response = self.get_response(**kwargs)
#         self.assertIsNotNone(response)
#         self.valid_data_exists(response, kwargs.get("window"))
#         return response

#     @test_utils.random_buildings(start=start, end=end, iterations=2, log_csv="price_energy_random_tests.csv", buildings=buildings, price_type="ENERGY")
#     def test_random_buildings(self, **kwargs):
#         response = self.get_response(**kwargs)
#         self.assertIsNotNone(response)
#         self.valid_data_exists(response, kwargs["window"])
#         return response

#     def random_one_building(self, building='ciee', price_type="ENERGY", window_unit="h"):
#         window = test_utils.generate_random_window(window_unit)
#         start, end = test_utils.generate_random_time_interval()
#         response = self.get_response(building=building, price_type=price_type, start=start,end=end,window=window)
#         self.assertIsNotNone(response)
#         self.valid_data_exists(response, window)

# if __name__ == '__main__':
#     test_loader = unittest.TestLoader()
#     test_names = test_loader.getTestCaseNames(TestPriceData)

#     suite = unittest.TestSuite()
#     for test_name in test_names:
#         suite.addTest(TestPriceData(test_name))

#     result = unittest.TextTestRunner().run(suite)

#     sys.exit(not result.wasSuccessful())
