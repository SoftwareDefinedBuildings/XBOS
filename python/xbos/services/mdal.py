import msgpack
import pytz
import pandas as pd
import uuid
import time
from datetime import timedelta, datetime
import threading
import random
import capnp
import data_capnp
from bw2python import ponames
from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
from xbos.util import pretty_print_timedelta, TimeoutException
RAW  = 0
MEAN = 1 << 1
MIN = 1 <<  2
MAX = 1 << 3
COUNT = 1 << 4

DEFAULT_TIMEOUT=30
class MDALClient(object):
    """
    Simple Python client for the Metadata-Driven-Access-Layer (MDAL).
    MDAL ties together Brick models and timeseries data through the use of the `brickframe:uuid`
    relationship in the Brick model. The idea is this should replace tieing together HodDB
    and Pundat manually
    """

    def __init__(self, url, client=None, timeout=30):
        """
        Creates an MDAL client.

        Arguments:
        [url]: the BOSSWAVE uri where mdal is hosted
        [client]: if this is None, we use environment vars to configure a client
                  automatically; else, we use the client provided from bw2python
        """
        if client is None:
            client = Client()
            client.vk = client.setEntityFromEnviron()
            client.overrideAutoChainTo(True)
        if not isinstance(client, Client):
            raise TypeError("first argument must be bw2python.client.Client or None")
        self.c = client
        self.vk = client.vk
        self.url = url

        # check liveness
        responses = self.c.query("{0}/*/s.mdal/!meta/lastalive".format(url))
        for resp in responses:
            # get the metadata records from the response
            md_records = filter(lambda po: po.type_dotted == ponames.PODFSMetadata, resp.payload_objects)
            # get timestamp field from the first metadata record
            last_seen_timestamp = msgpack.unpackb(md_records[0].content).get('ts')
            # get how long ago that was
            now = time.time()*1e9 # nanoseconds
            # convert to microseconds and get the timedelta
            diff = timedelta(microseconds = (now - last_seen_timestamp)/1e3)
            print "Saw [{0}] MDAL {1}".format(self.url, pretty_print_timedelta(diff))
            if diff.total_seconds() > timeout:
                raise TimeoutException("MDAL at {0} is too old".format(self.url))

    def do_query(self, query, timeout=DEFAULT_TIMEOUT, tz=pytz.timezone("US/Pacific")):
        """
        Query structure is as follows:

        query = {
            # We bind UUIDs found as the result of a Brick query to a variable name
            # that we can use later.
            # Each variable definition has the following:
            #  - name: how we will refer to this group of UUIDs
            #  - definition: a Brick query. The SELECT clause should return variables that end in '_uuid', which can be found as the
            #          object of a 'bf:uuid' relationship
            #  - units: what units we want to retrieve this stream as. Currently supports W/kW, Wh/kWh, F/C, Lux
            "Variables": [
                {"Name": "meter",
                 "Definition": "SELECT ?meter_uuid WHERE { ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter . ?meter bf:uuid ?meter_uuid . };",
                 "Units": "kW",
                },
                {"Name": "temp",
                 "Definition": "SELECT ?temp_uuid WHERE { ?temp rdf:type/rdfs:subClassOf* brick:Temperature_Sensor . ?temp bf:uuid ?temp_uuid . };",
                 "Units": "F",
                },
            ],

            # this is the composition of the data matrix we are returning. Below, all the uuids for the "meter" variable will be placed before
            # all of the uuids for the "temp" variable. We cannot guarantee order of uuids within those groups, but the ordering of the groups
            # will be preserved. Explicit UUIDs can also be used here
            "Composition": ["meter", "temp"],

            # If we are retrieving statistical data, then we need to say which statistical elements we want to download.
            # The options are RAW, MEAN, MIN, MAX and COUNT. To query multiple, you can OR them together (e.g. MEAN|MAX).
            # This maps 1-1 to the "Composition" field
            "Selectors": [MEAN, MEAN],

            # Themporal parameters for the query. Retrieves data in the range [T0, T1]. By convention, T0 < T1,
            # but MDAL will take care of it if this is reversed.
            # WindowSize is the size of the resample window in nanoseconds
            # if Aligned is true, then MDAL will snap all data to the begining of the window (e.g. if 5min window + Aligned=true,
            # then all timestamps will be on 00:05:00, 00:10:00, 00:15:00, etc)
            "Time": {
                "T0": "2017-08-01 00:00:00",
                "T1": "2017-08-08 00:00:00",
                "WindowSize": '2h',
                "Aligned": True,
            },
        }
        """
        nonce = str(random.randint(0, 2**32))
        query['Nonce'] = nonce
        ev = threading.Event()
        response = {}
        def _handleresult(msg):
            got_response = False
            for po in msg.payload_objects:
                if po.type_dotted == (2,0,10,4):
                    data = msgpack.unpackb(po.content)
                    if data['Nonce'] != query['Nonce']:
                        continue
                    if 'error' in data:
                        response['error'] = data['error']
                        response['df'] = None
                        got_response=True
                        continue
                    uuids = [str(uuid.UUID(bytes=x)) for x in data['Rows']]
                    data = data_capnp.StreamCollection.from_bytes_packed(data['Data'])
                    if hasattr(data, 'times') and len(data.times):
                        times = list(data.times)
                        if len(times) == 0:
                            response['df'] = pd.DataFrame(columns=uuids)
                            got_response = True
                            break
                        df = pd.DataFrame(index=pd.to_datetime(times, unit='ns', utc=False))
                        for idx, s in enumerate(data.streams):
                            df[uuids[idx]] = s.values
                        df.index = df.index.tz_localize(pytz.utc).tz_convert(tz)
                        response['df'] = df
                        got_response = True
                    else:
                        for idx, s in enumerate(data.streams):
                            if hasattr(s, 'times'):
                                s = pd.Series(s.values, pd.to_datetime(list(s.times), unit='ns', utc=False))
                                s.index = s.index.tz_localize(pytz.utc).tz_convert(tz)
                            else:
                                s = pd.Series(s.values)
                            response[uuids[idx]] = s
                        got_response = True
            if got_response:
                ev.set()
        h = self.c.subscribe("{0}/s.mdal/_/i.mdal/signal/{1}".format(self.url, self.vk[:-1]), _handleresult)
        po = PayloadObject((2,0,10,3), None, msgpack.packb(query))
        self.c.publish("{0}/s.mdal/_/i.mdal/slot/query".format(self.url), payload_objects=(po,))
        ev.wait(timeout)
        self.c.unsubscribe(h)
        if 'error' in response:
            raise Exception(response['error'])
        return response

if __name__ == '__main__':
    query = {
        "Composition": ["meter", "temp"],
        "Selectors": [MEAN, MEAN],
        "Variables": [
            {"Name": "meter",
             "Definition": "SELECT ?meter_uuid WHERE { ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter . ?meter bf:uuid ?meter_uuid . };",
             "Units": "kW",
            },
            {"Name": "temp",
             "Definition": "SELECT ?temp_uuid WHERE { ?temp rdf:type/rdfs:subClassOf* brick:Temperature_Sensor . ?temp bf:uuid ?temp_uuid . };",
             "Units": "F",
            },
        ],
        "Time": {
            "T0": "2017-08-01 00:00:00 PST",
            "T1": "2017-08-08 00:00:00 PST",
            "WindowSize": int(1e9*60*5),
            "Aligned": True,
        },
        "Params": {
            "Statistical": False,
            "Window": True,
        },
    }

    c = MDALClient("xbos/mdal")
    df = c.do_query(query)['df']
    print df.describe()
