import xbos_services_utils3 as utils
import datetime
import pytz

import sys
sys.path.append("/..")
from server import *


building = 'ciee'
zone = "HVAC_Zone_Northzone"

end = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
start = end - datetime.timedelta(hours=2)

all_bldgs = utils.get_buildings()


s_time = time.time()


date = pytz.timezone("America/Los_Angeles").localize(datetime.datetime(2017, 01, 01))
utc_date = date.astimezone(pytz.utc)

print(date)

print(get_all_occ("ciee", "HVAC_Zone_Eastzone",
                      date, date + datetime.timedelta(days=10), 60*15))

print(get_all_occ("ciee", "HVAC_Zone_Eastzone",
              utc_date, utc_date + datetime.timedelta(days=10), 60*15))

print(_get_week_occupancy("ciee", "HVAC_Zone_Eastzone",
                      date,60*60))

print("")



print(get_all_occ("ciee", "HVAC_Zone_Eastzone",
                      utc_date, end  15*60))

print(utils.decrement_to_start_of_day(date, float(3/100.*60)))


print("Time", time.time() - s_time)

for bldg in all_bldgs:
# case 1, Test from now into future
print("Building: %s" % bldg)
for zone in utils.get_zones(bldg):
    s_time = time.time()
    print("Zone: %s" % zone)

    # d_start = datetime.datetime(2018, 01, 01).replace(tzinfo=pytz.utc)
    # end = d_start + datetime.timedelta(days=6)

    print(get_all_occ(bldg, zone,
                      date, date + datetime.timedelta(days=10), 60 * 15))

    print(get_all_occ(bldg, zone,
                      utc_date, utc_date + datetime.timedelta(days=10), 60 * 15))


    print("Took: %f seconds" % (time.time() - s_time))


print("")
