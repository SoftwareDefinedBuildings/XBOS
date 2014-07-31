from smap import actuate, driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import math

class Controller(driver.SmapDriver):
    def setup(self, opts):
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        self.sp = float(opts.get('setpoint',78))
        self.db = float(opts.get('deadband',1))
        self.rate = float(opts.get('rate',1))

        # Initialize controller state
        self.cur_temp = self.sp
        self.state = 0          # initial cool is off

        # subscribe to zone air temperature
        self.zonepath = opts.pop('zonepath','/room/airtemp')
        self.siteid = opts.pop('zonesiteid','')
        restriction = "Path = '{0}'".format(self.zonepath)
        if self.siteid :
            restriction = restriction + " and Metadata/Site/id = '{0}'".format(self.siteid)
        self.roomclient = RepublishClient(self.archiver_url, self.controlcb, restrict=restriction)

        # create timeseries for contoller actions
        self.add_timeseries('/cool', 'On/Off', data_type='long')

    def start(self):
        self.roomclient.connect()
        periodicSequentialCall(self.read).start(self.rate)

    # Periodically schedule controller event
    #  - update control state
    #  - build timeseries of actions
    def read(self):
        if (self.cur_temp > self.sp + self.db) : self.state = 1 # start cool
        if (self.cur_temp < self.sp - self.db) : self.state = 0 # stop cool
        self.add('/cool', self.state) # publish the state change

    # Handle temperature reporting event
    #  record most recent zone temperature for next contol event
    def controlcb(self, _, data):
        mostrecent = data[-1][-1]
        self.cur_temp = mostrecent[1]
