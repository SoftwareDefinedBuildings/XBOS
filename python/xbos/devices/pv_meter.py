
import time
import msgpack

from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
from xbos.util import read_self_timeout

class PV_Meter(object):
    def __init__(self, client=None, uri=None):
        self.client = client
        self._uri = uri.rstrip('/')
        self._state = {
         "current_power": None,
         "time": None,
         "total_energy_lifetime": None,
         "total_energy_today": None,
        }
        def _handle(msg):
            for po in msg.payload_objects:
                if po.type_dotted == (2,1,1,6):
                    data = msgpack.unpackb(po.content)
                    for k,v in data.items():
                        self._state[k] = v
        # check liveness
        liveness_uri = "{0}/!meta/lastalive".format(uri)
        res = self.client.query(liveness_uri)
        if len(res) == 0:
            raise Exception("No liveness message found at {0}. Is this URI correct?".format(liveness_uri))
        alive = msgpack.unpackb(res[0].payload_objects[0].content)
        ts = alive['ts'] / 1e9
        if time.time() - ts > 30:
            raise Exception("{0} more than 30sec old. Is this URI current?".format(liveness_uri))
        print "Got PV_Meter at {0} last alive {1}".format(uri, alive['val'])

        self.client.subscribe("{0}/signal/info".format(uri), _handle)

    @property
    def current_power(self, timeout=30):
        return read_self_timeout(self, 'current_power', timeout)

    @property
    def total_energy_lifetime(self, timeout=30):
        return read_self_timeout(self, 'total_energy_lifetime', timeout)

    @property
    def total_energy_today(self, timeout=30):
        return read_self_timeout(self, 'total_energy_today', timeout)


    def write(self, state):
        po = PayloadObject((2,1,1,6), None, msgpack.packb(state))
        self.client.publish('{0}/slot/state'.format(self._uri),payload_objects=(po,))
