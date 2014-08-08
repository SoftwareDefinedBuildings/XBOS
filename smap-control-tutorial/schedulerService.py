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
import schedule
import time

testschedules = {'weekday': (('morning', '7:30', {'heatSetpoint':70, 'coolSetpoint': 74}),
                             ('night',  '20:30', {'heatSetpoint':60, 'coolSetpoint': 76})),
                 'weekend': (('morning', '9:30', {'heatSetpoint':68, 'coolSetpoint': 74}),
                             ('evening','17:00', {'heatSetpoint':68, 'coolSetpoint': 76}),
                             ('night',  '21:00', {'heatSetpoint':58, 'coolSetpoint': 78}))}

class Scheduler(driver.SmapDriver):
    def setup(self, opts):
        self.rate = float(opts.get('rate',15))
        self.sched = schedule.scheduler(testschedules)         

        # initialize weekly schedule - uses date.weekday convention
        self.weekly = ('weekday','weekday','weekday','weekday','weekday','weekend','weekend')
        self.schedule = 'none'
        self.epoch = 'none'

        # Current state of the points
        self.points = {}
        self.points['heatSetpoint']=int(opts.get('defaultHeatSetpoint',68))
        self.points['coolSetpoint']=int(opts.get('defaultCoolSetpoint',76))

        # create timeseries for scheduler actions
        heatSetPoint = self.add_timeseries('/heatSetpoint', 'F', data_type='long')
        coolSetPoint = self.add_timeseries('/coolSetpoint', 'F', data_type='long')

        # ought to have schedule and epoch be timeseries too.  This forces enumerate
        heatSetPoint.add_actuator(setpointActuator(scheduler=self, range=(40,90)))
        coolSetPoint.add_actuator(setpointActuator(scheduler=self, range=(40,90)))

    def start(self):

        periodicSequentialCall(self.read).start(self.rate)

    # Periodically check the schedule
    #   when there is a change publish to thermostats, will persist till new epoch or overide
    def read(self):
        now = time.localtime()
        scheduleName = self.weekly[now.tm_wday]
        self.epoch, self.points = self.sched.getPoints(scheduleName, now.tm_hour, now.tm_min)
        for (point,val) in self.points.iteritems() :
            if (self.points[point] != val) :
                self.points[point] = val
                self.add('/'+point, val)


class setpointActuator(actuate.ContinuousActuator):
    def __init__(self, **opts):
        actuate.ContinuousActuator.__init__(self, range=(40,100))
        self.scheduler = opts.get('scheduler')

    def get_state(self, request):
        return self.scheduler.points

    def set_state(self, request, val):
        print "set state", request, val
#        self.scheduler.sp = val
        return state



        

