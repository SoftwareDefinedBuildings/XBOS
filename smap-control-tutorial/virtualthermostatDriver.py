from smap import driver, actuate
from smap.archiver.client import RepublishClient
from smap.util import periodicSequentialCall

class VirtualThermostat(driver.SmapDriver):
    def setup(self, opts):
        self.state = {'temp': 70,
                      'humidity': 50,
                      'hvac_state': 1,
                      'temp_heat': 70,
                      'temp_cool': 75,
                      'hold': 0,
                      'override': 0,
                      'hvac_mode': 1,
                      'fan_mode': 1,
                      }

        self.readperiod = float(opts.get('ReadPeriod',3))
        self.add_timeseries('/temp', 'F', data_type='long') 
        self.add_timeseries('/humidity', '%RH', data_type='long') 
        self.add_timeseries('/hvac_state', 'Mode', data_type='long') 
        temp_heat = self.add_timeseries('/temp_heat', 'F', data_type='long') 
        temp_cool = self.add_timeseries('/temp_cool', 'F', data_type='long') 
        hold = self.add_timeseries('/hold', 'On/Off', data_type='long') 
        override = self.add_timeseries('/override', 'On/Off', data_type='long') 
        hvac_mode = self.add_timeseries('/hvac_mode', 'Mode', data_type='long') 
        fan_mode = self.add_timeseries('/fan_mode', 'Mode', data_type='long') 

        temp_heat.add_actuator(SetpointActuator(tstat=self, path='temp_heat', _range=(45, 95)))
        temp_cool.add_actuator(SetpointActuator(tstat=self, path='temp_cool', _range=(45, 95)))
        hold.add_actuator(OnOffActuator(tstat=self, path='hold'))
        override.add_actuator(OnOffActuator(tstat=self, path='override'))
        hvac_mode.add_actuator(ModeActuator(tstat=self, path='hvac_mode', states=[0,1,2,3]))
        fan_mode.add_actuator(OnOffActuator(tstat=self, path='fan_mode'))

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


        metadata_type = [
                ('/temp','Sensor'),
                ('/humidity','Sensor'),
                ('/temp_heat','Reading'),
                ('/temp_heat_act','SP'),
                ('/temp_cool','Reading'),
                ('/temp_cool_act','SP'),
                ('/hold','Reading'),
                ('/hold_act','Command'),
                ('/override','Reading'),
                ('/override_act','Command'),
                ('/hvac_mode','Reading'),
                ('/hvac_mode_act','Command')
            ]
        for ts, tstype in metadata_type:
            self.set_metadata(ts,{'Metadata/Type':tstype})

    def start(self):
        self.heatSPclient.connect() # activate subscription scheduler setpoints
        self.coolSPclient.connect() 
        periodicSequentialCall(self.read).start(self.readperiod)

    def read(self):
        for k,v in self.state.iteritems():
            self.add('/'+k, v)

    # Event handler for publication to heatSP stream
    def heatSPcb(self, _, data):
        # list of arrays of [time, val]
        mostrecent = data[-1][-1] 
        self.heatSP = mostrecent[1]
        print "Set heating setpoint", self.heatSP
        self.state['temp_heat'] = self.heatSP

    def coolSPcb(self, _, data):
        # list of arrays of [time, val]
        mostrecent = data[-1][-1] 
        self.coolSP = mostrecent[1]
        print "Set cooling setpoint", self.coolSP
        self.state['temp_cool'] = self.coolSP

class VirtualThermostatActuator(actuate.SmapActuator):
    def __init__(self, **opts):
        self.tstat = opts.get('tstat')
        self.path = opts.get('path')

class SetpointActuator(VirtualThermostatActuator, actuate.ContinuousIntegerActuator):
    def __init__(self, **opts):
        actuate.ContinuousIntegerActuator.__init__(self, opts['_range'])
        VirtualThermostatActuator.__init__(self, **opts)

    def get_state(self, request):
        return self.tstat.state[self.path]
    
    def set_state(self, request, state):
        self.tstat.state[self.path] = int(state)
        return self.tstat.state[self.path]

class ModeActuator(VirtualThermostatActuator, actuate.NStateActuator):
    def __init__(self, **opts):
        actuate.NStateActuator.__init__(self, opts['states'])
        VirtualThermostatActuator.__init__(self, **opts)

    def get_state(self, request):
        return self.tstat.state[self.path]
    
    def set_state(self, request, state):
        self.tstat.state[self.path] = int(state)
        return self.tstat.state[self.path]

class OnOffActuator(VirtualThermostatActuator, actuate.BinaryActuator):
    def __init__(self, **opts):
        actuate.BinaryActuator.__init__(self)
        VirtualThermostatActuator.__init__(self, **opts)

    def get_state(self, request):
        return self.tstat.state[self.path]
    
    def set_state(self, request, state):
        self.tstat.state[self.path] = int(state)
        return self.tstat.state[self.path]
