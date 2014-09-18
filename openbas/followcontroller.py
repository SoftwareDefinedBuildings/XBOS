from smap.services.zonecontroller import ZoneController

class FollowMaster(ZoneController):
    def setup(self, opts):
        ZoneController.setup(self, opts)
        self.add_timeseries('/temp_heat','F',data_type='double')
        self.add_timeseries('/temp_cool','F',data_type='double')

    def step(self):
        print 'ZONE CONTROL',self.points
        self.add('/temp_heat', float(self.points['temp_heat']))
        self.add('/temp_cool', float(self.points['temp_cool']))
