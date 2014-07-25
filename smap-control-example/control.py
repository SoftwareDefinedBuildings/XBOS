from smap import actuate, driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import random
import math

from controllogic import cool_controller

class Controller(driver.SmapDriver):
    def setup(self, opts):
        # source of streaming data
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        # streaming data uuid
        self.roomuuid = opts.get('roomuuid')
        # subscribe to datastream
        restriction = "uuid = '{0}'".format(self.roomuuid)
        self.roomclient = RepublishClient(self.archiver_url, self.controlcb, restrict=restriction)
        # setpoint
        self.sp = float(opts.get('setpoint',78))
        # deadband
        self.db = float(opts.get('deadband',1))
        # period between calling controller
        self.rate = float(opts.get('rate',1))

        self.add_timeseries('/cool', 'On/Off',data_type='long')

        # initialize current temperature to setpoint
        self.cur_temp = self.sp

        self.cool_controller = cool_controller

    def start(self):
        self.roomclient.connect()
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        # calculate and send control decision
        print self.cool_controller(self.cur_temp, self.sp, self.db)
        self.add('/cool', self.cool_controller(self.cur_temp, self.sp, self.db))

    def controlcb(self, _, data):
        # parse streaming data
        mostrecent = data[-1][-1]
        self.cur_temp = mostrecent[1]
