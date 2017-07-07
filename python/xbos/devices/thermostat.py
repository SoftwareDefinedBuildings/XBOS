import msgpack
from bw2python.bwtypes import PayloadObject
import time

class Thermostat(object):
    def __init__(self, client=None, uri=None):
        """
        Instantiates an XBOS thermostat

        [client]: a BW2 Client instance
        [uri]: the base uri (ending in i.xbos.thermostat) 
        """
        self.client = client
        self._uri = uri.rstrip('/') # strip trailing slash
        self._state = {
            'heating_setpoint': None,
            'cooling_setpoint': None,
            'temperature': None,
            'relative_humidity': None,
            'override': None,
            'fan': None,
            'mode': None,
            'state': None,
        }
        def _handle(msg):
            for po in msg.payload_objects:
                if po.type_dotted == (2,1,1,0):
                    data = msgpack.unpackb(po.content)
                    for k,v in data.items():
                        self._state[k] = v
                    
        self.client.subscribe("{0}/signal/info".format(uri), _handle)

    @property
    def heating_setpoint(self):
        while self._state.get('heating_setpoint') is None:
            time.sleep(1)
        return self._state.get('heating_setpoint')

    @property
    def cooling_setpoint(self):
        while self._state.get('cooling_setpoint') is None:
            time.sleep(1)
        return self._state.get('cooling_setpoint')

    @property
    def temperature(self):
        while self._state.get('temperature') is None:
            time.sleep(1)
        return self._state.get('temperature')

    @property
    def relative_humidity(self):
        while self._state.get('relative_humidity') is None:
            time.sleep(1)
        return self._state.get('relative_humidity')

    @property
    def override(self):
        while self._state.get('override') is None:
            time.sleep(1)
        return self._state.get('override')

    @property
    def fan(self):
        while self._state.get('fan') is None:
            time.sleep(1)
        return self._state.get('fan')

    @property
    def mode(self):
        while self._state.get('mode') is None:
            time.sleep(1)
        return self._state.get('mode')

    @property
    def state(self):
        while self._state.get('state') is None:
            time.sleep(1)
        return self._state.get('state')

    @property
    def time(self):
        while self._state.get('time') is None:
            time.sleep(1)
        return self._state.get('time')

    def write(self, state):
        po = PayloadObject((2,1,1,0),None,msgpack.packb(state))
        self.client.publish('{0}/slot/state'.format(self._uri),payload_objects=(po,))

    def set_heating_setpoint(self, value):
        self.write({'heating_setpoint': value})
    def set_cooling_setpoint(self, value):
        self.write({'cooling_setpoint': value})
    def set_override(self, value):
        self.write({'override': value})
    def set_mode(self, value):
        self.write({'mode': value})
    def set_fan(self, value):
        self.write({'fan': value})
