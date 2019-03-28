from __future__ import print_function

import grpc
import time
import datetime
import calendar
import pytz
import sys
import yaml
import math
from pathlib import Path
sys.path.append(str(Path.cwd().parent))
import indoor_temperature_action_pb2
import indoor_temperature_action_pb2_grpc
import unittest
import test_utils as utils

class TestActionData(unittest.TestCase):   

    def __init__(self, test_name, stub):
        super(TestActionData, self).__init__(test_name)
        self.stub = stub
        self.buildings = utils.get_buildings()
        self.zones = utils.get_zones_by_building()

    def get_response(self, building="ciee", zone="HVAC_Zone_Eastzone", window="1h", start=-1, end=-1):
        try:
            if start == -1 or end == -1:
                now = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
                end = int(time.mktime(now.timetuple()) * 1e9)
                before = now - datetime.timedelta(days=10)
                start = int(time.mktime(before.timetuple()) * 1e9)

                # alternate start and end times below
                # start = int(time.mktime(datetime.datetime.strptime("30/09/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
                # end = int(time.mktime(datetime.datetime.strptime("1/10/2018 0:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
            return self.stub.GetRawActions(indoor_temperature_action_pb2.Request(building=building, zone=zone, start=start,end=end,window=window))
        except grpc.RpcError as e:
            print(e)
    
    def response_exists(self, response):
        self.assertIsNotNone(response)
        self.assertIsInstance(obj=response, cls=indoor_temperature_action_pb2.RawActionReply)
       
    
    def valid_data_exists(self, response, window):
        last_time = 0
        for action in response.actions:
            self.assertIsNotNone(action)
            self.assertIsNotNone(action.time)
            self.assertIsNotNone(action.action)
            self.assertIsInstance(obj=action, cls=indoor_temperature_action_pb2.ActionPoint)
            self.assertIsInstance(obj=action.time, cls=int)
            self.assertIsInstance(obj=action.action, cls=float)
            last_time = self.window_is_accurate(last_time, action.time, window)
    
    def window_is_accurate(self, last_time, cur_time, window):
        if last_time != 0:
            time_diff = cur_time - last_time
            time_delta = utils.window_to_timedelta(window)
            self.assertEqual(time_diff, time_delta.total_seconds() * 1e9)

        return cur_time
        
    def test_all_buildings_and_zones(self):
        no_data = {}
        window = "1h"
        for building in self.buildings:
            for zone in self.zones[building]:
                response = self.get_response(building=building, zone=zone, window=window)

                if response is None:
                    if building in no_data:
                        no_data[building].append(zone)
                    else:
                        no_data[building] = [zone]
                else:
                    print(building, zone)
                    self.response_exists(response)
                    self.valid_data_exists(response, window)
        
        with open('no_action_data.yml', 'w') as outfile:
            yaml.dump(no_data, outfile)
                   

if __name__ == '__main__':
    with grpc.insecure_channel('localhost:50060') as channel:
        stub = indoor_temperature_action_pb2_grpc.IndoorTemperatureActionStub(channel)

        test_loader = unittest.TestLoader()
        test_names = test_loader.getTestCaseNames(TestActionData)

        suite = unittest.TestSuite()
        for test_name in test_names:
            suite.addTest(TestActionData(test_name, stub))

        result = unittest.TextTestRunner().run(suite)

        sys.exit(not result.wasSuccessful())
