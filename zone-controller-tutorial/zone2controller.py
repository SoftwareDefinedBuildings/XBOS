from smap.services.zonecontroller import ZoneController

class FollowMaster(ZoneController):
    def setup(self, opts):
        ZoneController.setup(self, opts)
        self.add_timeseries('/temp_heat','F',data_type='double')
        self.add_timeseries('/temp_cool','F',data_type='double')

    def step(self):
        self.add('/temp_heat', self.points['temp_heat'] + 5)
        self.add('/temp_cool', self.points['temp_cool'] + 5)
