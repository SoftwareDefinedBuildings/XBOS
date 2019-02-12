building = 'ciee'
zone = "HVAC_Zone_Northzone"

end = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
start = end - datetime.timedelta(hours=2)

bw_client = Client()
bw_client.setEntityFromEnviron()
bw_client.overrideAutoChainTo(True)
hod_client = HodClient("xbos/hod", bw_client)
mdal_client = mdal.MDALClient("xbos/mdal")


date = pytz.timezone("America/Los_Angeles").localize(datetime.datetime(2017, 01, 01, minute=54))
utc_date = date.astimezone(pytz.utc)

print(date)

# print(_get_week_do_not_exceed("ciee", "HVAC_Zone_Eastzone",
#                           date, date + datetime.timedelta(days=10), 60*15))
#
print(get_band("ciee", "HVAC_Zone_Eastzone",
              utc_date, utc_date + datetime.timedelta(days=10, minutes=2), 60*13, "do_not_exceed"))

print(get_band("ciee", "HVAC_Zone_Eastzone",
              utc_date, utc_date + datetime.timedelta(days=10, minutes=-1), 60*15, "do_not_exceed"))

# res = _get_week_comfortband("ciee", "HVAC_Zone_Eastzone",
#                           date,60*15)

print("")
