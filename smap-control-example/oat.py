from smap import driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import math

class OAT(driver.SmapDriver):
    def setup(self, opts):
        # initial temperature
        self.start_temp = float(opts.pop('start_temp','80'))
        # period between polling sensor
        self.rate = float(opts.pop('rate','1'))
        self.jump = float(opts.pop('jump','1'))
        self.curtemp = self.start_temp

        self.t = 1

        self.add_timeseries('/temperature','F',data_type='double')

    def start(self):
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        # temperature calculated as a parametric sine wave
        self.t += 1
        self.curtemp = 78 + 10*math.sin(.01 * self.t)
        self.add('/temperature', self.curtemp)

