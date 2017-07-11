import msgpack
from bw2python.bwtypes import PayloadObject
import time
from xbos.util import read_self_timeout

class Light(object):
    def __init__(self, client=None, uri=None):
        """
        Instantiates an XBOS light

        [client]: a BW2 Client instance
        [uri]: the base uri (ending in i.xbos.light) 
        """
        self.client = client
        self._uri = uri.rstrip('/') # strip trailing slash
        self._state = {
            'state': None,
            'time': None,
            'brightness': None,
        }
        def _handle(msg):
            for po in msg.payload_objects:
                if po.type_dotted == (2,1,1,1):
                    data = msgpack.unpackb(po.content)
                    for k,v in data.items():
                        self._state[k] = v
                    
        self.client.subscribe("{0}/signal/info".format(uri), _handle)

    @property
    def state(self, timeout=30):
        return read_self_timeout(self, 'state',timeout)

    @property
    def time(self, timeout=30):
        return read_self_timeout(self, 'time',timeout)

    @property
    def brightness(self, timeout=30):
        return read_self_timeout(self, 'brightness',timeout)

    def write(self, state):
        po = PayloadObject((2,1,1,1),None,msgpack.packb(state))
        self.client.publish('{0}/slot/state'.format(self._uri),payload_objects=(po,))

    def set_state(self, value):
        self.write({'state': value})

    def set_brightness(self, value):
        self.write({'brightness': value})

