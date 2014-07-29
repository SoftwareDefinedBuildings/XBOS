from smap import actuate, driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import random
import math

class Room(driver.SmapDriver):
    def badclient(self, resp):
        print "Error connecting: ", resp

    def setup(self, opts):
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        self.oatpath = opts.pop('OATpath','/OAT/temperature')
        self.coolpath = opts.pop('coolpath', '/control/cool')
        self.siteid = opts.pop('siteid','')

        # Subscription to OAT stream, registering a callback
        restriction = "Path = '{0}'".format(self.oatpath)
        if self.siteid :
            restriction = restriction + " and Metadata/Site/id = '{0}'".format(self.siteid)
        self.oatclient = RepublishClient(self.archiver_url, self.oatcb, restrict=restriction, connect_error=self.badclient)

        # subscribe to the cool control stream
        restriction = "Path = '{0}'".format(self.coolpath)
        if self.siteid :
            restriction = restriction + " and Metadata/Site/id = '{0}'".format(self.siteid)

        self.coolclient = RepublishClient(self.archiver_url, self.coolcb, restrict=restriction, connect_error=self.badclient)

        # initalize parameters for the room model
        self.rate = float(opts.get('rate',1)) # model update rate
        self.therm_resistance = float(opts.get('therm_resistance', .1)) # thermal resistance factor
        self.e = float(opts.get('epsilon',.1))       # cooling factor

        # initial state of the room
        self.temp = float(opts.get('starttemp', 75)) # initial room 
        self.oat_val = self.temp
        self.cool = 0

        # Create the timeseries for the pseudo air temp sensor
        self.add_timeseries('/airtemp','F',data_type='double')

    # start the driver
    def start(self):
        self.oatclient.connect() # activate subscription to OAT stream'
        self.coolclient.connect() # activate subscription to cool stream
        periodicSequentialCall(self.read).start(self.rate) # schedule model periodically

    # Model simple physics of a room with heating across a thermally
    # resistant barrier and forced cooling
    def read(self):
        dt = (self.oat_val - self.temp)
#        self.temp = self.oat_val + 2.3 # little test during debugging
        self.temp = self.temp + self.rate * self.therm_resistance * dt - self.cool*self.e*dt
        self.add('/airtemp', self.temp) # add new value to the airtemp stream

    # Event handler for publication to OAT stream
    def oatcb(self, _, data):
        # list of arrays of [time, val]
        mostrecent = data[-1][-1] 
        self.oat_val = mostrecent[1]

    # Event handler for publication to cool stream
    def coolcb(self, _, data):
        mostrecent = data[-1][-1]
        self.cool = mostrecent[1]
