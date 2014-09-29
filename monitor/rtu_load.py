from smap.archiver.client import SmapClient
import time
import pandas as pd
#pd.options.display.mpl_style = 'default'

client = SmapClient('http://ciee.cal-sdb.org:8079')
# timestamps
end = int(time.time())
start = end - 60*60*24*30 # last month
print start, end

def get_demand():
    # get energy data for same timeframe
    res = client.query('select uuid where Metadata/System = "Monitoring" and Properties/UnitofMeasure = "kW"')
    uuids = [x['uuid'] for x in res]
    data = dict(zip(uuids,client.data_uuid(uuids, start, end, cache=False)))

    # create dataframe, use time as index
    demand = pd.DataFrame(data.values()[0])
    demand[0] = pd.to_datetime(demand[0], unit='ms')
    demand.index = demand[0]
    del demand[0]
    return demand

def get_hvacstates():
    # get all hvac_state timeseries
    res = client.query('select uuid where Metadata/System = "HVAC" and Properties/UnitofMeasure = "Mode" and Path like "%hvac_state"')
    uuids = [x['uuid'] for x in res]
    data = dict(zip(uuids,client.data_uuid(uuids, start, end, cache=False)))

    ret = {}

    for uuid in data.iterkeys():
        hvac = pd.DataFrame(data[uuid])
        hvac[0] = pd.to_datetime(hvac[0], unit='ms')
        hvac.index = hvac[0]
        del hvac[0]
        zone = client.query("select Metadata/HVACZone where uuid = '{0}'".format(uuid))[0]['Metadata']['HVACZone']
        ret[zone] = hvac
    return ret


if __name__ == '__main__':
    demand = get_demand()
    hvacs = get_hvacstates()
    for zone,hvac in hvacs.iteritems():
        # resample every minute
        hvac_rs = hvac.resample('10S',pd.np.max)
        demand_rs = demand.resample('10S',pd.np.max)
        # join on the timestamps to filter out missing data
        merge = hvac_rs.merge(demand_rs, left_index=True, right_index=True)
        merge.columns = ['state','demand']
        print len(merge)
        merge.plot(figsize=(30,10)).get_figure().savefig('{0}.png'.format(zone))
