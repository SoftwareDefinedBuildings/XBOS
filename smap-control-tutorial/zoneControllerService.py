"""
Copyright (c) 2014, Regents of the University of California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions 
are met:

 - Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
 - Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the
   distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS 
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL 
THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, 
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED 
OF THE POSSIBILITY OF SUCH DAMAGE.
"""
"""
@author David Culler <culler@berkeley.edu>
"""
from smap import actuate, driver
from smap.util import periodicSequentialCall
from smap.archiver.client import RepublishClient
from smap.archiver.client import SmapClient
import time
from pprint import pprint
from smap.contrib import dtutil

class ZoneController(driver.SmapDriver):
    def setup(self, opts):
        self.rate = float(opts.get('rate',10))
        # Current state of the points
        self.heatSP=int(opts.get('defaultHeatSetpoint',68))
        self.coolSP=int(opts.get('defaultCoolSetpoint',76))

        self.therm_temp = 70

        self.trim = int(opts.get('trim',0)) # dummy zoneCtrl action

        # create timeseries for zone controller actions
        heatSetPoint = self.add_timeseries('/heatSetpoint', 'F', data_type='double')
        coolSetPoint = self.add_timeseries('/coolSetpoint', 'F', data_type='double')
        # add actuators to them
        heatSetPoint.add_actuator(setpointActuator(controller=self, range=(40,90)))
        coolSetPoint.add_actuator(setpointActuator(controller=self, range=(40,90)))

        # get master set point stream paths
        self.archiver_url = opts.get('archiver_url','http://localhost:8079')
        self.heatSPwhere = opts.get('heatSPwhere', '')
        self.coolSPwhere = opts.get('coolSPwhere', '')
        self.thermwhere = opts.get('thermwhere', '')
        self.tempwhere = opts.get('tempwhere', '')

        print "ZoneController: heat sp where = ", self.heatSPwhere
        print "ZoneController: cool sp where = ", self.coolSPwhere
        print "ZoneController: thermostat where = ", self.thermwhere
        print "ZoneController: temp sensor where = ", self.tempwhere

        self.client = SmapClient(self.archiver_url)

        self.heatSPclient = RepublishClient(self.archiver_url, self.heatSPcb, restrict=self.heatSPwhere)
        self.coolSPclient = RepublishClient(self.archiver_url, self.coolSPcb, restrict=self.coolSPwhere)
        #self.tempclient = RepublishClient(self.archiver_url, self.tempcb, restrict=self.tempwhere)
        self.thermclient = RepublishClient(self.archiver_url, self.thermcb, restrict=self.thermwhere)


    def start(self):
        print "zone controller start: ", self.rate
        self.heatSPclient.connect() # activate subscription scheduler setpoints
        self.coolSPclient.connect() 
        #self.tempclient.connect() 
        self.thermclient.connect() 
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        all_readings = self.client.latest(self.tempwhere)
        for p in all_readings:
            print '-'*20
            md = self.client.tags('uuid = "'+p['uuid']+'"')[0]
            print 'Room:', md['Metadata/Room']
            print 'Reading:', p['Readings'][0][1]
            ts = dtutil.ts2dt(p['Readings'][0][0]/1000)
            print 'Time:', dtutil.strftime_tz(ts, tzstr='America/Los_Angeles')
        avg_room_temp = sum([x['Readings'][0][1] for x in all_readings]) / float(len(all_readings))

        # get difference between avg room temperature and thermostat temperature
        new_diff = self.therm_temp - avg_room_temp

        # periodically update output streams.  Here a bogus adjustment
        self.add('/heatSetpoint', self.heatSP + new_diff)
        self.add('/coolSetpoint', self.coolSP + new_diff)
        print "zone controller publish: ", self.heatSP, self.coolSP

    # Event handler for publication to heatSP stream
    def heatSPcb(self, _, data):
        # list of arrays of [time, val]
        print "ZoneController heatSPcb: ", data
        mostrecent = data[-1][-1] 
        self.heatSP = mostrecent[1]

    def coolSPcb(self, _, data):
        # list of arrays of [time, val]
        print "ZoneController coolSPcb: ", data
        mostrecent = data[-1][-1] 
        self.coolSP = mostrecent[1]

    def tempcb(self, _, data):
        # list of arrays of [time, val]
        print "ZoneController tempcb: ", data


    def thermcb(self, _, data):
        # list of arrays of [time, val]
        print "ZoneController thermcb: ", data
        self.therm_temp = data[-1][-1][1]



class setpointActuator(actuate.ContinuousActuator):
    def __init__(self, **opts):
        actuate.ContinuousActuator.__init__(self, range=(40,100))
        self.controller = opts.get('controller')

    def get_state(self, request):
        return self.controller.heatSP, self.controller.coolSP

    def set_state(self, request, val):
        print "set state", request, val
        # do something here
        return self.controller.heatSP, self.controller.coolSP




        

