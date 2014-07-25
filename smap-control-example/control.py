from smap import actuate, driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import random
import math

from controllogic import cool_controller

class Controller(driver.SmapDriver):
    def setup(self, opts):
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        self.sp = float(opts.get('setpoint',78))
        self.db = float(opts.get('deadband',1))
        self.rate = float(opts.get('rate',1))
        self.roomuuid = opts.get('roomuuid')
        restriction = "uuid = '{0}'".format(self.roomuuid)
        self.roomclient = RepublishClient(self.archiver_url, self.controlcb, restrict=restriction)
        self.add_timeseries('/cool', 'On/Off',data_type='long')
        self.cur_temp = self.sp

        self.cool_controller = cool_controller

    def start(self):
        self.roomclient.connect()
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        print self.cool_controller(self.cur_temp, self.sp, self.db)
        self.add('/cool', self.cool_controller(self.cur_temp, self.sp, self.db))

    def controlcb(self, _, data):
        mostrecent = data[-1][-1]
        self.cur_temp = mostrecent[1]
