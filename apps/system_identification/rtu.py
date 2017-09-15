from xbos import get_client
# for interacting with archiver
from xbos.services.pundat import DataClient, timestamp, make_dataframe, merge_dfs
# for performing Brick queries
from xbos.services.hod import HodClient
# for interacting with the thermostat control state
from xbos.devices.thermostat import Thermostat

# get a bosswave client
c = get_client() # defaults to $BW2_AGENT, $BW2_DEFAULT_ENTITY

# get a HodDB client
hod = HodClient("ciee/hod", c)
# get an archiver client
archiver = DataClient(c,archivers=["ucberkeley"])


zone2tstat = {}
# query for the the thermostat APIs
query = """
SELECT ?thermostat ?zone ?uri WHERE {
    ?thermostat rdf:type/rdfs:subClassOf* brick:Thermostat .
    ?zone rdf:type brick:HVAC_Zone .

    ?thermostat bf:controls/bf:feeds+ ?zone .
    ?thermostat bf:uri ?uri .
};"""
for row in hod.do_query(query)["Rows"]:
    zone = row["?zone"]
    uri = row["?uri"]
    zone2tstat[zone] = Thermostat(c, uri)
