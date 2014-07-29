# Pseudo outside air temperature driver
# Produces a stream of values varying around a given point
#
# Configuration parameters example
#
# [/oat]
# type=pseudoOATdriver.OAT
# start=80 - initial temperature
# rate=1   - period of report
# jump=2   - width of variation
#
from smap import driver
from smap.util import periodicSequentialCall
import math

class OAT(driver.SmapDriver):
    def setup(self, opts):
        self.starttemp = float(opts.pop('start_temp','80'))
        self.rate = float(opts.pop('rate','1'))
        self.jump = float(opts.pop('jump','2'))
        self.curtemp = self.starttemp
        self.t = 1
        self.add_timeseries('/temperature','F',data_type='double')

    def start(self):
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        self.t += 1
        self.curtemp = self.starttemp + self.jump*math.sin(.01 * self.t)
        self.add('/temperature', self.curtemp)

