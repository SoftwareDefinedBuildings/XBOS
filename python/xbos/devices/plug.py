import msgpack
from bw2python.bwtypes import PayloadObject
import time
from xbos.util import read_self_timeout

class Plug(object):
    def __init__(self, client=None, uri=None):
        """
        Instantiates an XBOS plug

        [client]: a BW2 Client instance
        [uri]: the base uri (ending in i.xbos.plug) 
        """
        self.client = client
        self._uri = uri.rstrip('/') # strip trailing slash
        self._state = {
            'state': None,
            'time': None,
            'voltage': None,
            'current': None,
            'power': None,
            'cumulative': None,
        }
        def _handle(msg):
            for po in msg.payload_objects:
                if po.type_dotted == (2,1,1,2):
                    data = msgpack.unpackb(po.content)
                    for k,v in data.items():
                        self._state[k] = v
                    
        self.client.subscribe("{0}/signal/info".format(uri), _handle)

    @property
    def state(self):
        return read_self_timeout(self, 'state',timeout)

    @property
    def time(self):
        return read_self_timeout(self, 'time',timeout)

    @property
    def voltage(self):
        return read_self_timeout(self, 'voltage',timeout)

    @property
    def current(self):
        return read_self_timeout(self, 'current',timeout)

    @property
    def power(self):
        return read_self_timeout(self, 'power',timeout)

    @property
    def cumulative(self):
        return read_self_timeout(self, 'cumulative',timeout)

    def write(self, state):
        po = PayloadObject((2,1,1,2),None,msgpack.packb(state))
        self.client.publish('{0}/slot/state'.format(self._uri),payload_objects=(po,))

    def set_state(self, value):
        self.write({'state': value})
