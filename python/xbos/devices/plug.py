import msgpack
from bw2python.bwtypes import PayloadObject
import time

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
        while self._state.get('state') is None:
            time.sleep(1)
        return self._state.get('state')

    @property
    def time(self):
        while self._state.get('time') is None:
            time.sleep(1)
        return self._state.get('time')

    @property
    def voltage(self):
        while self._state.get('voltage') is None:
            time.sleep(1)
        return self._state.get('voltage')

    @property
    def current(self):
        while self._state.get('current') is None:
            time.sleep(1)
        return self._state.get('current')

    @property
    def power(self):
        while self._state.get('power') is None:
            time.sleep(1)
        return self._state.get('power')

    @property
    def cumulative(self):
        while self._state.get('cumulative') is None:
            time.sleep(1)
        return self._state.get('cumulative')

    def write(self, state):
        po = PayloadObject((2,1,1,2),None,msgpack.packb(state))
        self.client.publish('{0}/slot/state'.format(self._uri),payload_objects=(po,))

    def set_state(self, value):
        self.write({'state': value})
