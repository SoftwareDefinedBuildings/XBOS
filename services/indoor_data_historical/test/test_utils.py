import xbos_services_utils3 as utils
import datetime

def get_buildings():
    return utils.get_buildings()

def get_zones_by_building():
    buildings = get_buildings()
    zones = {}

    for building in buildings:
        zones[building] = utils.get_zones(building)

    return zones

def window_to_timedelta(window):
    unit = window[-1]
    time = float(window[:-1])

    if unit == 'h':
        return datetime.timedelta(hours=time)
    elif unit == 'm':
        return datetime.timedelta(minutes=time)
    elif unit == 's':
        return datetime.timedelta(seconds=time)
    elif unit == 'd':
        return datetime.timedelta(days=time)
    elif unit == 'y':
        return datetime.timedelta(weeks=time*52)
    elif unit == 'w':
        return datetime.timedelta(weeks=time)
    