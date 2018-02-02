import msgpack
import shutil
import os
import docker
import time
import threading
import random
import requests
import json
from datetime import timedelta, datetime

from bw2python import ponames
from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
from xbos.util import pretty_print_timedelta, TimeoutException

DEFAULT_TIMEOUT=30

class HodClientHTTP(object):
    def __init__(self, url="http://localhost:47808"):
        self.url = url
    def do_query(self, query, values_only=True):
        url = self.url+'/api/query'
        resp = requests.post(url, data=query)
        if not resp.ok:
            raise Exception("Query to {0} failed ({1})".format(self.url, resp.reason))
        d = resp.json()
        count = d['Count']
        elapsed = d['Elapsed']
        rows = d['Rows']
        if values_only and int(count) > 0:
            rows = [{k: v['Value'] for k,v in r.items()} for r in rows]
        return rows

class HodClient(object):
    def __init__(self, url, client=None, timeout=20):
        if client is None:
            client = Client()
            client.vk = client.setEntityFromEnviron()
            client.overrideAutoChainTo(True)
        if not isinstance(client, Client):
            raise TypeError("first argument must be bw2python.client.Client or None")
        self.c = client
        self.vk = client.vk
        self.url = url

        responses = self.c.query("{0}/*/s.hod/!meta/lastalive".format(url))
        for resp in responses:
            # get the metadata records from the response
            md_records = filter(lambda po: po.type_dotted == ponames.PODFSMetadata, resp.payload_objects)
            # get timestamp field from the first metadata record
            last_seen_timestamp = msgpack.unpackb(md_records[0].content).get('ts')
            # get how long ago that was
            now = time.time()*1e9 # nanoseconds
            # convert to microseconds and get the timedelta
            diff = timedelta(microseconds = (now - last_seen_timestamp)/1e3)
            print "Saw [{0}] HodDB {1}".format(self.url, pretty_print_timedelta(diff))
            if diff.total_seconds() > timeout:
                raise TimeoutException("HodDB at {0} is too old".format(self.url))

    def do_query(self, query, timeout=DEFAULT_TIMEOUT, values_only=True):
        nonce = str(random.randint(0, 2**32))
        ev = threading.Event()
        response = {}
        def _handleresult(msg):
            # decode, throw away if not correct nonce
            got_response = False
            # if got response
            for po in msg.payload_objects:
                if po.type_dotted == (2,0,10,2):
                    data = msgpack.unpackb(po.content)

                    if data["Nonce"] != nonce:
                        continue
                    data.pop("Nonce")

                    if data["Error"] is not None and len(data["Error"]) > 0:
                        raise Exception(data["Error"])
                    else:
                        data.pop("Error")

                    for k,v in data.items():
                        response[k] = v
                    if values_only and response["Count"] > 0:
                        response["Rows"] = [{k: v["Value"] for k,v in r.items()} for r in response["Rows"]]
                    got_response = True
            if got_response:
                ev.set()
        h = self.c.subscribe("{0}/s.hod/_/i.hod/signal/result".format(self.url), _handleresult)
        q_struct = msgpack.packb({"Query": query, "Nonce": nonce})
        po = PayloadObject((2,0,10,1), None, q_struct)
        self.c.publish("{0}/s.hod/_/i.hod/slot/query".format(self.url), payload_objects=(po,))
        ev.wait(timeout)
        self.c.unsubscribe(h)
        if len(response) == 0: # no results
            raise TimeoutException("Query of {0} timed out".format(query))

        return response

class LocalHodDB(HodClientHTTP):
    def __init__(self, buildings):
        print buildings

        # make config directory
        shutil.rmtree('/tmp/_hoddb', ignore_errors=True)
        os.makedirs('/tmp/_hoddb')
        _build = ""
        for dbname, filename in buildings.items():
            newdest = os.path.join('/tmp/_hoddb', os.path.basename(filename))
            mountname = os.path.join('/etc/hod', os.path.basename(filename))
            shutil.copy(filename, newdest)
            _build += "    {0}: {1}\n".format(dbname, mountname)
        with open('/tmp/_hoddb/hodconfig.yaml','wb') as f:
            f.write(_CONFIG.format(_build))

        self.client = docker.from_env()
        # pull latest hod
        self.client.images.pull('gtfierro/hod:0.5.6')
        try:
            c = self.client.containers.get('localhod')
            c.kill()
            c.remove()
        except docker.errors.NotFound:
            pass

        self.container = self.client.containers.run('gtfierro/hod:0.5.6',
                                                volumes={'/tmp/_hoddb': {'bind': '/etc/hod',' mode': 'rw'}},
                                                name='localhod',
                                                detach=True)
        while True:
            self.container.reload()
            if '0.0.0.0:47808' in self.container.logs(tail='all'):
                break
        print 'ip addr', self.container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
        self.ip = self.container.attrs['NetworkSettings']['Networks']['bridge']['IPAddress']
        #print dir(container)
        #container.logs(follow=True)
        HodClientHTTP.__init__(self, url="http://{0}:47808".format(self.ip))

_CONFIG = """
### HodDB Configuration
# commented out lines are default configuration options
Buildings:
    {0}

# the path to the TTL file containing Brick relationships
BrickFrameTTL: "/BrickFrame.ttl"
# the path to the TTL file containing Brick classes
BrickClassTTL: "/Brick.ttl"
DisableQueryCache: true

####
# Interface Enabling
####
# Enable HTTP server
EnableHTTP: true
# Enable BOSSWAVE server
EnableBOSSWAVE: false

####
# configuration for verbosity during operation
####
# Show the full latency of the query (and its larger components)
ShowQueryLatencies: true
# Set log level. In order of increasing verbosity:
# Debug, Info, Notice, Warning, Error, Critical
LogLevel: Debug


####
# HTTP Server Configuration
####
# port to run the server on
ServerPort: 47808
# Whether or not to serve on localhost. If false, serves on a public interface
ListenAddress: 0.0.0.0
# Path to the server directory of hod, which contains the necessary HTML files
StaticPath: /server

# If specified, serve the frontend over HTTPS using golang.org/x/crypto/acme/autocert
# If left blank (default), just serve over HTTP
#TLSHost: ""

####
# BOSSWAVE Server Configuration
####
# Base URI
HodURI: scratch.ns/hod
"""
