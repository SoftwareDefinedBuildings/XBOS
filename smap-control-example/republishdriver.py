from smap import actuate, driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import random
import math

from controllogic import cool_controller

class RepubDriver(driver.SmapDriver):

    def setup(self, opts):
        self.subscription_uuid = opts.pop('uuid','33294f4c-23a4-5c10-a798-33c13a24ea53')
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        self.repubclient = RepublishClient(self.archiver_url, self.cb, restrict="uuid = '{0}'".format(self.subscription_uuid))

        self.add_timeseries("/test", "V", data_type="long")

    def cb(self, _, data):
        for x in data[0]:
            self.add('/test', x[1]+50)

    def start(self):

        print self.repubclient
        print self.archiver_url
        self.repubclient.connect()
        #from twisted.internet import reactor
        #from threading import Thread
        #Thread(target=reactor.run, args=(False,)).start()

class OAT(driver.SmapDriver):
    def setup(self, opts):
        self.starttemp = float(opts.pop('start_temp','80'))
        self.rate = float(opts.pop('rate','1'))
        self.jump = float(opts.pop('jump','1'))
        self.curtemp = self.starttemp

        self.t = 1

        self.add_timeseries('/temperature','F',data_type='double')

    def start(self):
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        self.t += 1
        self.curtemp = 78 + 10*math.sin(.01 * self.t)
        self.add('/temperature', self.curtemp)

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

class Room(driver.SmapDriver):
    def setup(self, opts):
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        self.oatuuid = opts.get('oatuuid')
        restriction = "uuid = '{0}'".format(self.oatuuid)
        self.oatclient = RepublishClient(self.archiver_url, self.oatcb, restrict=restriction)

        self.cooluuid = opts.get('cooluuid')
        restriction = "uuid = '{0}'".format(self.cooluuid)
        self.coolclient = RepublishClient(self.archiver_url, self.coolcb, restrict=restriction)

        self.rate = float(opts.get('rate',1))
        self.therm_resistance = float(opts.get('therm_resistance', .1))
        self.temp = float(opts.get('starttemp', 75))
        self.e = float(opts.get('epsilon',.1))

        self.oat_val = 0
        self.coolstate = 0
        self.cool = 0

        self.add_timeseries('/currenttemp','F',data_type='double')

    def start(self):
        self.oatclient.connect()
        self.coolclient.connect()
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        dt = (self.oat_val - self.temp)
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




