from smap import actuate, driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import random
import math

class Room(driver.SmapDriver):
    def setup(self, opts):
        # source of streaming data
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        # streaming data uuid
        self.oatuuid = opts.get('oatuuid')
        # subscribe to datastream
        restriction = "uuid = '{0}'".format(self.oatuuid)
        self.oatclient = RepublishClient(self.archiver_url, self.oatcb, restrict=restriction)

        self.cooluuid = opts.get('cooluuid')
        restriction = "uuid = '{0}'".format(self.cooluuid)
        self.coolclient = RepublishClient(self.archiver_url, self.coolcb, restrict=restriction)

        # rate between recalculating room model
        self.rate = float(opts.get('rate',1))
        # thermal resistance of room
        self.therm_resistance = float(opts.get('therm_resistance', .1))
        # initial temperature of room
        self.temp = float(opts.get('starttemp', 75))
        # epsilon for room (for cooling)
        self.e = float(opts.get('epsilon',.1))

        # state vars
        self.oat_val = 0
        self.cool = 0

        self.add_timeseries('/currenttemp','F',data_type='double')

    def start(self):
        self.oatclient.connect()
        self.coolclient.connect()
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        dt = (self.oat_val - self.temp)
        print self.temp, self.rate, self.therm_resistance, self.cool,self.e
        self.temp = self.temp + self.rate * self.therm_resistance * dt - self.cool*self.e*dt
        self.add('/currenttemp', self.temp)

    def oatcb(self, _, data):
        # list of arrays of [time, val]
        mostrecent = data[-1][-1]
        self.oat_val = mostrecent[1]

    def coolcb(self, _, data):
        # list of arrays of [time, val]
        mostrecent = data[-1][-1]
        self.cool = mostrecent[1]
        print 'am i cooling', self.cool
