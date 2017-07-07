import msgpack
from bw2python.bwtypes import PayloadObject
import time

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
    def state(self):
        while self._state.get('state') is None:
            time.sleep(1)
        return self._state.get('state')

    @property
    def time(self):
        while self._state.get('time') is None:
            time.sleep(1)
        return self._state.get('time')

    @property
    def brightness(self):
        while self._state.get('brightness') is None:
            time.sleep(1)
        return self._state.get('brightness')

    def write(self, state):
        po = PayloadObject((2,1,1,1),None,msgpack.packb(state))
        self.client.publish('{0}/slot/state'.format(self._uri),payload_objects=(po,))

    def set_state(self, value):
        self.write({'state': value})

    def set_brightness(self, value):
        self.write({'brightness': value})

