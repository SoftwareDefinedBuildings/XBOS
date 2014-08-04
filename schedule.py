"""
Copyright (c) 20142, Regents of the University of California
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

from copy import copy

def cvt(hr,mn) :return hr+mn/60.0

class scheduler():
    """
    Scheduler class to hold and manage a set of named schedules, 
    each constisting of an ordered sequence of named epochs 
    with a start time, as '<hour>:<min>', and a dictionary of <pointname>:value

    """
    schedules = {}

    def __init__(self, initial={}) :
        """
        Create a scheduler, optionally with a dict of schedules
        {<scheduleName>:((<epochName>,<start>,{<point:<val>})*)*}

        traverses initial schedules to validate and transfer to internal representation
        
        """
        for schedName, sched in initial.iteritems() :
            self.addSchedule(schedName, sched)

    def getSchedules(self) :
        """ 
        Return the sequence of schedule names in the scheduler
        """
        return [name for name, schedule in self.schedules.iteritems()]

    def getSchedule(self, scheduleName) :
        """ 
        Return the list of (<name>,<start>,<points>) epochs for the named schedule
        """
        return copy(self.schedules[scheduleName]) if scheduleName in self.schedules else {}

    def addSchedule(self, scheduleName, schedule) :
        """ 
        Add a schedule to the scheduler, replacing any schedule with the same name
        """
        self.schedules[scheduleName] = [(name, start, points) for name, start, points in schedule]

    def delSchedule(self,scheduleName) :
        """ 
        Delete a schedule for the scheduler
        """
        del self.schedules[scheduleName]

    def getPoints(self, scheduleName, hour, minute) :
        """ 
        Return the epoch name, points for the epoch covered by the specified time
        """
        # Lookup named schedule in schedules database
        # Return: (epoch, points)
        #  epoch: name of the epoch containing hour:minute
        #  points: dictionary of points for the prior enclosing epoch
        #  'none', {} if schedule or enclosing epoch does not exist
        epoch, prev = 'none', {}
        target = cvt(hour, minute)
        if (scheduleName in self.schedules) :
            schedule = self.schedules[scheduleName]
            for ep,start,points in schedule :
                hr,mn = start.split(':')
                nextTime = cvt(int(hr),int(mn))
                if (target < nextTime) : break
                epoch, prev = ep, points
        return epoch, copy(prev)
        
    def getFinalPoints(self, scheduleName) :
        """ 
        Return the epoch name, points for the final epoch in a schedule

        This is useful for constructing cyclic schedules
        """
        if (scheduleName in self.schedules) :
            schedule = self.schedules[scheduleName]
            name, start, points = schedule[-1]
            return name, copy(points)
        else :
            return 'none',{}

    def generateDay(self, scheduleName, minutes=30, initial='') :
        """
        Generate and iterator that will produce a periodic series
        of eopch,points for an day under a schedule

        initial, if provided, starts the series with the final epoch of the 
        specified schedule
        """
        name, state = 'none', {}
        if initial : name, state = self.getFinalPoints(initial) 
        for m in range(0,24*60,minutes) :
            hour = m/60
            min = m - hour*60
            ename, points = self.getPoints(scheduleName,hour,min)
            if ename != 'none' : name = ename
            for point, val in points.iteritems() : state[point] = val
            yield (hour, min, name, state)

if __name__ == '__main__':
    testschedules = {'weekday': (
            ('morning', '7:30', {'setpoint':72, 'light':'on'}),
            ('evening','17:00', {'setpoint':75, 'light':'on'}),
            ('night',  '20:30', {'setpoint':54, 'light':'off'})
            ),
                     'weekend': (
            ('morning', '9:30', {'setpoint':71, 'light':'on'}),
            ('evening','17:00', {'setpoint':75, 'light':'on'}),
            ('night',  '21:00', {'setpoint':57, 'light':'off'})
            )
                     }
    s = scheduler(testschedules)
    for x in s.generateDay('weekday', 30, 'weekend') : print x


    
