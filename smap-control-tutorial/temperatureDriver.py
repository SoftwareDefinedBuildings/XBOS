from smap import driver
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall
import math

class Temperature(driver.SmapDriver):
    def setup(self, opts):
        self.starttemp = float(opts.pop('start_temp','72'))
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

