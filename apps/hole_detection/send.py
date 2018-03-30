import time
import pytz
from datetime import datetime, timedelta

# this is required for sending emails
import boto3
c = boto3.client('sns', region_name='us-east-2')

# XBOS services: Hod for getting UUIDs from query, MDAL for getting data
from xbos.services.hod import HodClient
hod = HodClient("xbos/hod")
import xbos.services.mdal as mdal
data = mdal.MDALClient("xbos/mdal")

# how many UUIDs to investigate at a time
CHUNK_UUID = 10
oldmsg = ""

# Here, we get the point names and corresponding UUIDs for all Brick models. We provide "values_only" to be False so that
# we can get the full URIs of the results, which can tell us which namespace the result is in.
# If we want to only do the scan for one namespace, we can change the "*" to that namespace
resp = hod.do_query("SELECT ?point ?uuid FROM * WHERE { ?point bf:uuid ?uuid };", values_only=False)
# extract UUIDs
uuids = [x['?uuid']['Value'] for x in resp['Rows']]
# extract point names as full URIs
points = [x['?point']['Namespace']+'#'+x['?point']['Value'] for x in resp['Rows']]

# Every 30 minutes, we initiate a scan of all the streams (identified by UUIDs) that we want to monitor. 
# We pull out 15-min aggregates of each stream from the last 30 minutes and see if there is any data in that range
while True:
    start = time.time()
    print "Starting scan of {0} uuids at {1}".format(len(uuids), datetime.now())
    msg = ""
    # iterate over the UUIDs in size of CHUNK_UUID
    for i in range(0, len(uuids), CHUNK_UUID):
        use_uuids = uuids[i:i+CHUNK_UUID]
        try:
            # issue query for historical data
            q = {
                "Composition": use_uuids,
                "Selectors": [mdal.MEAN]*len(use_uuids),
                "Time": {
                    "T1": (datetime.now(pytz.timezone('US/Pacific')) ).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "T0": (datetime.now(pytz.timezone('US/Pacific')) - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S %Z'),
                    "Aligned": True,
                    "WindowSize": "15min",
                },
            }
            resp = data.do_query(q)
            if 'error' in resp:
                print resp
                df = pd.DataFrame()
            else:
                # drop null values so we can just check the size of the data frame
                df = resp['df']
                df.dropna(inplace=True,how='all')

            # if there are no rows in the data frame, then add a formatted line to the output telling us what failed
            if not df.count().all():
                desc = '\n'.join(["{0}: {1}".format(uuids[x], points[x]) for x in range(i,i+CHUNK_UUID) if df[uuids[x]].count() == 0])
                msg += desc + '\n'
            end = time.time()
        except Exception as e:
            print 'exception',e

    # only send the email if the failed streams are different than last time (otherwise you get 48 emails per day!)
    if msg != "" and msg != oldmsg:
        oldmsg = msg
        msg = "No data in {0} - {1}".format(q["Time"]["T0"], q["Time"]["T1"]) + "\n"+msg

        print msg
        print "Emailing at", datetime.now()

        # line required to send email with failure
        c.publish(Message=msg, Subject="{0} XBOS Data Problem".format(datetime.now()), TopicArn="arn:aws:sns:us-east-2:459826155428:XBOS_DR_Data_Hole")

    # wait 30 minutes
    took = end - start
    wait = 1800 - took
    print 'took', took,'waiting',wait
    time.sleep(wait)
