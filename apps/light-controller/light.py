import time
from datetime import datetime
from collections import defaultdict
from xbos import get_client
from xbos.services.hod import HodClient
from xbos.devices.light import Light

c = get_client()
hod = HodClient("xbos/hod")
SITE = "ciee"

light_query = """SELECT ?light ?room ?light_uri FROM %s WHERE {
    ?light rdf:type brick:Lighting_System .
    ?light bf:feeds/bf:hasPart ?room .
    ?room rdf:type brick:Room .
    ?light bf:uri ?light_uri
};"""

res = hod.do_query(light_query % SITE)
print res
byrooms = defaultdict(list)
lights = set([
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d444/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d433/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d432/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d458/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d455/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d454/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d438/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor00d56d/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor013263/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor30005f/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01935b/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01902e/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01907b/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02309c/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01942b/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor018ff9/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01934e/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01930e/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor019324/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d429/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d454/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d455/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d444/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d438/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d432/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d433/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor00d56d/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor30005f/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d458/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor013263/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01935b/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01902e/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01907b/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02309c/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01942b/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor018ff9/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01934e/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor01930e/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor019324/i.xbos.light',
'gvnMwdNvhD5ClAuF8SQzrp-Ywcjx9c1m4du9N5MRCXs=/devices/enlighted/s.enlighted/Sensor02d429/i.xbos.light'])

all_lights = []
#for item in res['Rows']:
#    print item['?light'], item['?room']
#    l = Light(c, item['?light_uri'])
#    byrooms[item['?room']].append(l)
#    all_lights.append(l)
for light in lights:
    l = Light(c, light)
    all_lights.append(l)

from IPython import embed; embed()
old_brightnesses = []


for light in all_lights:
    old_brightnesses.append(light.brightness)
print 'saved old'

## first turn all lights to 75%
#print 'set 75%', datetime.now()
#for light in all_lights:
#    light.set_brightness(75)
#
## wait 20 min
#time.sleep(60*20)

print 'set 50%', datetime.now()
# then turn all lights to 50%
for light in all_lights:
    if light.brightness > 25:
        light.set_brightness(25)

# wait 20 min
time.sleep(60*60)

#print 'set 25%', datetime.now()
## then turn all lights to 25%
#for light in all_lights:
#    light.set_brightness(25)
#
## wait 20 min
#time.sleep(60*20)

#print 'reset', datetime.now()
## then turn all lights to 0%
#for light in all_lights:
#    light.set_brightness(0)
#
## wait 20 min
#time.sleep(60*20)


# reset old brightnesses
for idx, light in enumerate(all_lights):
    light.set_brightness(old_brightnesses[idx])

print byrooms.keys()
from IPython import embed; embed()
