from xbos import get_client
from xbos.services.pundat import DataClient, timestamp, make_dataframe
from xbos.services.hod import HodClient
from slackclient import SlackClient
import pandas as pd
import json
import sys
import time
import schedule

with open("params.json") as f:
    try:
        params = json.loads(f.read())
    except ValueError:
        print "Invalid parameter file"
        sys.exit(1)

# setup clients

client = get_client()
dataclient = DataClient(client, archivers=[params["ARCHIVER_URI"]])
hodclient = HodClient(params["HOD_URI"], client)
slack_token = params["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)

def notify(msg):
    sc.api_call("chat.postMessage",channel="#xbos_alarms",text=msg)

# get all thermostat states
query = """SELECT ?dev ?uri WHERE {
    ?dev rdf:type/rdfs:subClassOf* brick:Thermostat .
    ?dev bf:uri ?uri .
};"""
res = hodclient.do_query(query)
if res["Count"] == 0:
    print "no thermostats"
else:
    for row in res["Rows"]:
        print row["?uri"]

def get_building_meters():
    # get building meter and bosswave URIs
    query = """SELECT ?meter ?uri ?uuid WHERE {
        ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter .
        ?meter bf:uri ?uri .
        ?meter bf:uuid ?uuid .
    };"""

    res = hodclient.do_query(query)
    if res["Count"] == 0:
        print "No building meters found"
    meters = {} 
    all_meters = set([x["?uuid"] for x in res["Rows"]])

    # get device meters and bosswave URIs
    query = """SELECT ?device ?meter ?uuid WHERE {
        ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter .
        ?meter bf:uuid ?uuid .
        ?meter bf:isPointOf ?device .
        ?device rdf:type/rdfs:subClassOf* brick:Equipment .
    };"""

    res = hodclient.do_query(query)
    if res["Count"] == 0:
        print "No device meters found"
        return meters
    dev_meters = set([x["?uuid"] for x in res["Rows"])
    for row in res["Rows"]:
        meters[row["?device"]] = row["?uuid"]

    meters["building"] = list(all_meters - dev_meters)[0]
    return meters

def get_tstats():
    # get all thermostats
    query = """SELECT ?tstat ?zone ?uuid WHERE {
        ?tstat rdf:type/rdfs:subClassOf* brick:Thermostat .
        ?zone rdf:type brick:HVAC_Zone .
        ?p rdf:type brick:Mode_Status .

        ?tstat bf:hasPoint ?p .
        ?tstat bf:controls/bf:feeds ?zone .
        ?p bf:uuid ?uuid .
    };"""
    res = hodclient.do_query(query)
    if res["Count"] == 0:
        raise Exception("No thermostats found")
    tstats = {}
    zones = {}
    for row in res["Rows"]:
        tstats[row["?tstat"]] = row["?uuid"]
        zones[row["?uuid"]] = row["?zone"]
    return tstats, zones
        

def estimate_power_usage(d, meter_df):
    diffs = d['value'].diff()
    turnon = d[diffs > 0]
    turnoff = d[diffs < 0]
    sys.stderr.write("num on {0}, num off {1}".format(len(turnon), len(turnoff)))
    sys.stderr.flush()
    window = pd.Timedelta('20s')
    guesses = []
    for ts in turnon.index:
        # find biggest energy difference in a [-window, +window] slice around the state transition
        guess = meter_df.loc[ts-window:ts+window].diff().max().value
        if pd.isnull(guess) or guess == 0: continue
        guesses.append(guess)
    for ts in turnoff.index:
        # find biggest energy difference in a [-window, +window] slice around the state transition
        # negate it because this is the off->on signal, and use min()
        guess = -meter_df.loc[ts-window:ts+window].diff().min().value
        if pd.isnull(guess) or guess == 0: continue
        guesses.append(guess)
    guess = pd.np.median(guesses)
    if pd.isnull(guess): return 0.0
    return guess

def run():
    meter_uuids = get_building_meters()
    meter_dfs = make_dataframe(dataclient.data_uuids(meter_uuids['building'], "now", "now -1h"))
    for v in meter_dfs.values():
        print v.describe()

    tstat_uuids, zones = get_tstats()
    tstat_state_dfs = make_dataframe(dataclient.data_uuids(tstat_uuids.values(), "now", "now -1h"))

    building_meter_uuid = meter_uuids["building"]
    for uuid, tstat_df in tstat_state_dfs.items():
        usage = estimate_power_usage(tstat_df, meter_dfs[building_meter_uuid])
        sys.stderr.write("Estimator {0} ({1}) has prediction {2}".format(uuid, zones[uuid], usage))
        sys.stderr.flush()
        if usage != 0:
            notify("Estimator {0} ({1}) has prediction {2}".format(uuid, zones[uuid], usage))
        print uuid, usage
    

schedule.every(10).minutes.do(run)

run()
while True:
    schedule.run_pending()
    time.sleep(30)
