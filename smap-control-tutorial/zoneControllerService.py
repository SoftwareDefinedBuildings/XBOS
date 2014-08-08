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
import time

class ZoneController(driver.SmapDriver):
    def setup(self, opts):
        self.rate = float(opts.get('rate',10))
        # Current state of the points
        self.heatSP=int(opts.get('defaultHeatSetpoint',68))
        self.coolSP=int(opts.get('defaultCoolSetpoint',76))

        self.trim = int(opts.get('trim',0)) # dummy zoneCtrl action

        # create timeseries for zone controller actions
        heatSetPoint = self.add_timeseries('/heatSetpoint', 'F', data_type='long')
        coolSetPoint = self.add_timeseries('/coolSetpoint', 'F', data_type='long')
        # add actuators to them
        heatSetPoint.add_actuator(setpointActuator(controller=self, range=(40,90)))
        coolSetPoint.add_actuator(setpointActuator(controller=self, range=(40,90)))

        # get master set point stream paths
        self.archiver_url = opts.pop('archiver_url','http://localhost:8079')
        self.heatSPpath = opts.pop('heatSPpath', '/scheduler/heatSetpoint')
        self.coolSPpath = opts.pop('coolSPpath', '/scheduler/coolSetpoint')
# add mode
        self.siteid = opts.pop('siteid','')
        restriction = "Path = '{0}'".format(self.heatSPpath)
        if self.siteid :
            restriction = restriction + " and Metadata/Site/id = '{0}'".format(self.siteid)
        self.heatSPclient = RepublishClient(self.archiver_url, self.heatSPcb, restrict=restriction)
        restriction = "Path = '{0}'".format(self.coolSPpath)
        if self.siteid :
            restriction = restriction + " and Metadata/Site/id = '{0}'".format(self.siteid)
        self.coolSPclient = RepublishClient(self.archiver_url, self.coolSPcb, restrict=restriction)


    def start(self):
        self.heatSPclient.connect() # activate subscription scheduler setpoints
        self.coolSPclient.connect() 
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        # periodically update output streams
        self.add('/heatSetpoint', self.heatSP-self.trim)
        self.add('/coolSetpoint', self.coolSP+self.trim)

    # Event handler for publication to heatSP stream
    def heatSPcb(self, _, data):
        # list of arrays of [time, val]
        mostrecent = data[-1][-1] 
        self.heatSP = mostrecent[1]

    def coolSPcb(self, _, data):
        # list of arrays of [time, val]
        mostrecent = data[-1][-1] 
        self.coolSP = mostrecent[1]


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




        

