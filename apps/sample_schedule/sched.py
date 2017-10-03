import schedule
import datetime
import time

from xbos import get_client
from xbos.services.hod import HodClientHTTP
from xbos.devices.thermostat import Thermostat

client = get_client(entity="schedule.ent")
hc = HodClient("ciee/hod", client)

q = """SELECT ?uri ?zone WHERE {
    ?tstat rdf:type/rdfs:subClassOf* brick:Thermostat .
    ?tstat bf:uri ?uri .
    ?tstat bf:controls/bf:feeds ?zone .
};
"""

zones = {}
for tstat in hc.do_query(q):
    print tstat
    zones[tstat["?zone"]] = Thermostat(client, tstat["?uri"])

normal_zones = ["SouthZone","NorthZone","EastZone","CentralZone"]

def workday():
    p = {"override": True, "heating_setpoint": 70., "cooling_setpoint": 76.}
    print "workday",datetime.datetime.now()
    for z in normal_zones:
        print z,p
        zones[z].write(p)
def workday_inactive():
    p = {"override": True, "heating_setpoint": 62., "cooling_setpoint": 85.}
    print "workday inactive",datetime.datetime.now()
    for z in normal_zones:
        print z,p
        zones[z].write(p)

schedule.every().monday.at("08:00").do(workday)
schedule.every().tuesday.at("08:00").do(workday)
schedule.every().wednesday.at("08:00").do(workday)
schedule.every().thursday.at("08:00").do(workday)
schedule.every().friday.at("08:00").do(workday)

schedule.every().monday.at("18:00").do(workday_inactive)
schedule.every().tuesday.at("18:00").do(workday_inactive)
schedule.every().wednesday.at("18:00").do(workday_inactive)
schedule.every().thursday.at("18:00").do(workday_inactive)
schedule.every().friday.at("18:00").do(workday_inactive)


schedule.every().saturday.at("06:00").do(workday_inactive)
schedule.every().sunday.at("06:00").do(workday_inactive)

if __name__ == '__main__':
    workday()
    while True:
        schedule.run_pending()
        time.sleep(30)
