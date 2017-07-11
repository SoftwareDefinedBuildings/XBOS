import msgpack
from bw2python.bwtypes import PayloadObject
import time
from xbos.util import read_self_timeout

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
    def heating_setpoint(self, timeout=30):
        return read_self_timeout(self, 'heating_setpoint',timeout)

    @property
    def cooling_setpoint(self, timeout=30):
        return read_self_timeout(self, 'cooling_setpoint',timeout)

    @property
    def temperature(self, timeout=30):
        return read_self_timeout(self, 'temperature',timeout)

    @property
    def relative_humidity(self, timeout=30):
        return read_self_timeout(self, 'relative_humidity',timeout)

    @property
    def override(self, timeout=30):
        return read_self_timeout(self, 'override',timeout)

    @property
    def fan(self, timeout=30):
        return read_self_timeout(self, 'fan',timeout)

    @property
    def mode(self, timeout=30):
        return read_self_timeout(self, 'mode',timeout)

    @property
    def state(self, timeout=30):
        return read_self_timeout(self, 'state',timeout)

    @property
    def time(self, timeout=30):
        return read_self_timeout(self, 'time',timeout)

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
