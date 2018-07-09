import os
import pytz
import yaml

from xbos.services import hod, mdal

cfg = yaml.load(open('config.yml'))
AGENT = cfg.get('agent', '127.0.0.1:28589')
if AGENT.startswith('$'):
    AGENT = os.environ[AGENT]

ENTITY = cfg.get('entity', '')
if ENTITY.startswith('$'):
    ENTITY = os.environ[ENTITY[1:]]

SITE = cfg.get('site', 'ciee')

HOD = hod.HodClient(cfg.get('hod', 'xbos/hod'))

MDAL = mdal.MDALClient(cfg.get('mdal', 'xbos/mdal'))

TZ = pytz.timezone(cfg.get('tz', 'US/Pacific'))
