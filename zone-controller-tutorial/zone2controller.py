from smap.services.zonecontroller import ZoneController

class FollowMaster(ZoneController):
    def setup(self, opts):
        ZoneController.setup(self, opts)
        self.add_timeseries('/temp_heat','F',data_type='double')
        self.add_timeseries('/temp_cool','F',data_type='double')

    def step(self):
        """
        self.points contains the most recent advertised values
        for 'temp_haet' and 'temp_cool' from the master scheduler.
        We add 5 to these, and then republish to our end points
        """
        self.add('/temp_heat', float(self.points['temp_heat']) + 5)
        self.add('/temp_cool', float(self.points['temp_cool']) + 5)
