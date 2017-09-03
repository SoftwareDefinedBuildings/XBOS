import msgpack
import delorean
import threading
import random
import time
from datetime import timedelta, datetime

from bw2python import ponames
from bw2python.bwtypes import PayloadObject
from bw2python.client import Client
from xbos.util import pretty_print_timedelta, TimeoutException

DEFAULT_TIMEOUT=30

class DataClient(object):
    """
    Simple wrapper class for interacting with data services exposed over BOSSWAVE
    """
    def __init__(self, client=None, archivers=None):
        """
        Creates a BW2 Data client

        Arguments:
        [client]: if this is None, we use environment vars to configure a client
                  automatically; else, we use the client provided
        [archivers]: this is a list of base archiver URIs. These can be found by
                  running "pundat scan <namespace>"
        """
        # bw2 client
        if client is None:
            client = Client()
            client.vk = client.setEntityFromEnviron()
            client.overrideAutoChainTo(True)
        if not isinstance(client, Client):
            raise TypeError("first argument must be bw2python.client.Client or None")
        self.c = client
        self.vk = client.vk


        if archivers is None:
            archivers = ["ucberkeley"] # default archiver
        self.archivers = []
        # scan for archiver liveness
        for archiver in archivers:
            responses = self.c.query("{0}/*/s.giles/!meta/lastalive".format(archiver))
            for resp in responses:
                # get the metadata records from the response
                md_records = filter(lambda po: po.type_dotted == ponames.PODFSMetadata, resp.payload_objects)
                # get timestamp field from the first metadata record
                last_seen_timestamp = msgpack.unpackb(md_records[0].content).get('ts')
                # get how long ago that was
                now = time.time()*1e9 # nanoseconds
                # convert to microseconds and get the timedelta
                diff = timedelta(microseconds = (now - last_seen_timestamp)/1e3)
                print "Saw [{0}] archiver {1}".format(archiver, pretty_print_timedelta(diff))
                if diff.total_seconds() < 20:
                    self.archivers.append(archiver)
        if len(self.archivers) == 0:
            self.archivers = archivers

    def query(self, query, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        Runs the given pundat query and returns the results as a Python object.

        Arguments:
        [query]: the query string
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        if archiver == "":
            archiver = self.archivers[0]

        nonce = random.randint(0, 2**32)
        ev = threading.Event()
        response = {}
        def _handleresult(msg):
            # decode, throw away if not correct nonce
            got_response = False
            error = getError(nonce, msg)
            if error is not None:
                got_response = True
                response["error"] = error

            metadata = getMetadata(nonce, msg)
            if metadata is not None:
                got_response = True
                response["metadata"] = metadata

            timeseries = getTimeseries(nonce, msg)
            if timeseries is not None:
                got_response = True
                response["timeseries"] = timeseries

            if got_response:
                ev.set()

        vk = self.vk[:-1] # remove last part of VK because archiver doesn't expect it

        # set up receiving
        self.c.subscribe("{0}/s.giles/_/i.archiver/signal/{1},queries".format(archiver, vk), _handleresult)

        # execute query
        q_struct = msgpack.packb({"Query": query, "Nonce": nonce})
        po = PayloadObject((2,0,8,1), None, q_struct)
        self.c.publish("{0}/s.giles/_/i.archiver/slot/query".format(archiver), payload_objects=(po,))

        ev.wait(timeout)
        if len(response) == 0: # no results
            raise TimeoutException("Query of {0} timed out".format(query))
        return response

    def uuids(self, where, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        Using the given where-clause, finds all UUIDs that match

        Arguments:
        [where]: the where clause (e.g. 'path like "keti"', 'SourceName = "TED Main"')
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        resp = self.query("select uuid where {0}".format(where), archiver, timeout)
        uuids = []
        for r in resp["metadata"]:
            uuids.append(r["uuid"])
        return uuids

    def tags(self, where, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        Retrieves tags for all streams matching the given WHERE clause

        Arguments:
        [where]: the where clause (e.g. 'path like "keti"', 'SourceName = "TED Main"')
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        return self.query("select * where {0}".format(where), archiver, timeout).get('metadata',{})

    def tags_uuids(self, uuids, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        Retrieves tags for all streams with the provided UUIDs

        Arguments:
        [uuids]: list of UUIDs
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        if not isinstance(uuids, list):
            uuids = [uuids]
        where = " or ".join(['uuid = "{0}"'.format(uuid) for uuid in uuids])
        return self.query("select * where {0}".format(where), archiver, timeout).get('metadata',{})

    def data(self, where, start, end, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        With the given WHERE clause, retrieves all RAW data between the 2 given timestamps

        Arguments:
        [where]: the where clause (e.g. 'path like "keti"', 'SourceName = "TED Main"')
        [start, end]: time references:
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        return self.query("select data in ({0}, {1}) where {2}".format(start, end, where), archiver, timeout).get('timeseries',{})

    def data_uuids(self, uuids, start, end, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        With the given list of UUIDs, retrieves all RAW data between the 2 given timestamps

        Arguments:
        [uuids]: list of UUIDs
        [start, end]: time references:
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        if not isinstance(uuids, list):
            uuids = [uuids]
        where = " or ".join(['uuid = "{0}"'.format(uuid) for uuid in uuids])
        return self.query("select data in ({0}, {1}) where {2}".format(start, end, where), archiver, timeout).get('timeseries',{})

    def stats(self, where, start, end, pw, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        With the given WHERE clause, retrieves all statistical data between the 2 given timestamps, using the given pointwidth

        Arguments:
        [where]: the where clause (e.g. 'path like "keti"', 'SourceName = "TED Main"')
        [start, end]: time references:
        [pw]: pointwidth (window size of 2^pw nanoseconds)
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        return self.query("select statistical({3}) data in ({0}, {1}) where {2}".format(start, end, where, pw), archiver, timeout).get('timeseries',{})

    def stats_uuids(self, uuids, start, end, pw, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        With the given set of uuids, retrieves all statistical data between the 2 given timestamps, using the given pointwidth

        Arguments:
        [uuids]: list of UUIDs
        [start, end]: time references:
        [pw]: pointwidth (window size of 2^pw nanoseconds)
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        if not isinstance(uuids, list):
            uuids = [uuids]
        where = " or ".join(['uuid = "{0}"'.format(uuid) for uuid in uuids])
        return self.query("select statistical({3}) data in ({0}, {1}) where {2}".format(start, end, where, pw), archiver, timeout).get('timeseries',{})

    def window(self, where, start, end, width, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        With the given WHERE clause, retrieves all statistical data between the 2 given timestamps, using the given window size

        Arguments:
        [where]: the where clause (e.g. 'path like "keti"', 'SourceName = "TED Main"')
        [start, end]: time references:
        [width]: a time expression for the window size, e.g. "5s", "365d"
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        return self.query("select window({3}) data in ({0}, {1}) where {2}".format(start, end, where, width), archiver, timeout).get('timeseries',{})

    def window_uuids(self, uuids, start, end, width, archiver="", timeout=DEFAULT_TIMEOUT):
        """
        With the given set of uuids, retrieves all statistical data between the 2 given timestamps, using the given window size

        Arguments:
        [uuids]: list of UUIDs
        [start, end]: time references:
        [width]: a time expression for the window size, e.g. "5s", "365d"
        [archiver]: if specified, this is the archiver to use. Else, it will run on the first archiver passed
                    into the constructor for the client
        [timeout]: time in seconds to wait for a response from the archiver
        """
        if not isinstance(uuids, list):
            uuids = [uuids]
        where = " or ".join(['uuid = "{0}"'.format(uuid) for uuid in uuids])
        return self.query("select window({3}) data in ({0}, {1}) where {2}".format(start, end, where, width), archiver, timeout).get('timeseries',{})

def make_dataframe(result):
    """
    Turns the results of one of the data API calls into a pandas dataframe
    """
    import pandas as pd
    ret = {}
    if isinstance(result,dict):
        if 'timeseries' in result:
            result = result['timeseries']
    for uuid, data in result.items():
        df = pd.DataFrame(data)
        if len(df.columns) == 5: # statistical data
            df.columns = ['time','min','mean','max','count']
        else:
            df.columns = ['time','value']
        df['time'] = pd.to_datetime(df['time'],unit='ns')
        df = df.set_index(df.pop('time'))
        ret[uuid] = df
    return ret

def merge_dfs(dfs, resample=None, do_mean=False, do_sum=False, do_min=False, do_max=False):
    """
    dfs is a dictionary of key => dataframe
    This method resamples each of the dataframes if a period is provided
    (http://pandas.pydata.org/pandas-docs/stable/timeseries.html#offset-aliases)
    """
    if len(dfs) == 0:
        raise Exception("No dataframes provided")
    df = dfs.values()[0]
    name = dfs.keys()[0]
    df.columns = map(lambda x: name+"_"+x if not x.startswith(name) else x, df.columns)
    if resample is not None:
        df = df.resample(resample)
        if do_mean: df = df.mean()
        elif do_sum: df = df.sum()
        elif do_min: df = df.min()
        elif do_max: df = df.max()
        else: df = df.mean()
    if len(dfs) > 1:
        for name, newdf in dfs.items()[1:]:
            if resample is not None:
                newdf = newdf.resample(resample)
                if do_mean: newdf = newdf.mean()
                elif do_sum: newdf = newdf.sum()
                elif do_min: newdf = newdf.min()
                elif do_max: newdf = newdf.max()
                else: newdf = newdf.mean()
            newdf.columns = map(lambda x: name+"_"+x if not x.startswith(name) else x, newdf.columns)
            df = df.merge(newdf, left_index=True, right_index=True, how='outer')
    return df

def timestamp(thing, nanoseconds=False):
    if nanoseconds:
        return thing+"ns"
    if isinstance(thing, int) or isinstance(thing, float):
        # try to treat as a number
        return str(thing)
    else:
        return str(delorean.parse(thing).epoch)[:-2] + 's'

def getError(nonce, msg):
    for po in msg.payload_objects:
        if po.type_dotted == (2,0,8,9): # GilesQueryError
            data = msgpack.unpackb(po.content)
            if data["Nonce"] != nonce:
                continue
            return data
def getMetadata(nonce, msg):
    for po in msg.payload_objects:
        if po.type_dotted == (2,0,8,2): # GilesMetadataResult
            data = msgpack.unpackb(po.content)
            if data["Nonce"] != nonce:
                continue
            # fold the metadata records into the top-level scope for each document
            md = data["Data"]
            for idx, doc in enumerate(md):
                metadata = doc.pop("metadata")
                for k,v in metadata.items():
                    doc[k] = v
                md[idx] = doc
            return md
def getTimeseries(nonce, msg):
    for po in msg.payload_objects:
        if po.type_dotted == (2,0,8,4): # GilesTimeseriesResult
            data = msgpack.unpackb(po.content)
            if data["Nonce"] != nonce:
                continue
            if data["Data"]:
                ts_data = {}
                for res in data["Data"]:
                   ts_data[res["uuid"]]= zip(res["times"], res["values"])
                return ts_data
            if data["Stats"]:
                ts_data = {}
                for res in data["Stats"]:
                    ts_data[res["uuid"]] = zip(res["times"], res["min"], res["mean"], res["max"], res["count"])
                return ts_data
            return data
