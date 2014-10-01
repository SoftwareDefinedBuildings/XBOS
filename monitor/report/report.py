from smap.archiver.client import SmapClient
import time
import datetime
import json
import pandas as pd
#pd.options.display.mpl_style = 'default'

client = SmapClient('http://128.32.211.229:8079')
#client = SmapClient('http://ciee.cal-sdb.org:8079')
# timestamps
end = int(time.time())
start = end - 60*60*24*30 # last month

zones = client.query('select distinct Metadata/HVACZone')

def getdataasjson(query, start, end):
    tmp_data = client.data(query,start,end,cache=False,limit=100000)
    if not len(tmp_data[0]):
        return {}
    tmp = pd.DataFrame(tmp_data[1][0])
    if len(tmp.notnull()) == 0:
        return {}
    tmp[0] = pd.to_datetime(tmp[0], unit='ms')
    tmp.index = tmp[0]
    tmp = tmp[pd.np.abs(tmp[1] - tmp[1].mean()) <= 2*tmp[1].std()]
    del tmp[0]
    return json.loads(tmp.to_json())["1"]
    

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
    res = client.query('select uuid where Metadata/System = "HVAC" and Path like "%hvac_state"')
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

def get_zonetemps():
    # get all hvac_state timeseries
    res = client.query('select uuid where Metadata/System = "HVAC" and Path like "%temp"')
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


def group_contiguous(df, key, value):
    """
    condition: df[key] == value
    We need to create discrete groups based on a condition that exists for a contiguous region. In our case, we
    want to identify sections of indices of our dataframe [df] where the condition is met and the indexes are
    sequential

    Returns a list of tuples (before, start, end, after, condition):
    before: index before group
    start: first index where [condition] holds
    end: last index where [condition] holds
    after: index after group
    condition: is [condition] T/F?
    """
    # transitions is a list of indexes into [df] indicating the location before
    # [df] jumps from condition=True to condition=False (or vice-versa)
    conditions = pd.np.diff(df[key] == value)
    transitions = conditions.nonzero()[0]
    # pairs of indexes indicating the start/end of a group
    pairs = zip(transitions[:-1], transitions[1:])
    ret = []
    for start,end in pairs:
        ret.append((start,start+1,end,end+1,df.iloc[start+1][key] == value))
    return ret

def resample_and_merge():
    """
    Resamples every 5 seconds and merges the demand data with the zone data. Yields one dataframe
    for each zone
    """
    demand = get_demand()
    demand_rs = demand.resample('5S',pd.np.median,closed='left')
    hvacs = get_hvacstates()
    for zone,hvac in hvacs.iteritems():
        # resample every minute
        hvac_rs = hvac.resample('5S',pd.np.median,closed='left')
        # join on the timestamps to filter out missing data
        merge = hvac_rs.merge(demand_rs, left_index=True, right_index=True)
        merge.columns = ['state','demand']
        yield zone, merge

def resample_and_merge_cumulative():
    """
    Adds the HVAC states together, does 5second resampling and returns a single dataframe
    """
    demand = get_demand()
    demand_rs = demand.resample('5S',pd.np.median,closed='left')
    cumulative = demand_rs.copy()
    cumulative[1] = 0
    cumulative[1] = cumulative[1].fillna(0)
    hvacs = get_hvacstates()
    for zone,hvac in hvacs.iteritems():
        # resample every minute
        hvac_rs = hvac.resample('5S',pd.np.median,closed='left')
        # join on the timestamps to filter out missing data
        merge = hvac_rs.merge(demand_rs, left_index=True, right_index=True)
        merge.columns = ['state','demand']
        cumulative[1] += hvac_rs[1].fillna(0)
    merge['state'] = cumulative
    return merge

def plot_zones():
    for zone, merge in resample_and_merge():
        merge.plot(figsize=(30,10)).get_figure().savefig('{0}.png'.format(zone))

def plot_cumulative():
    merge = resample_and_merge_cumulative()
    fig = merge.plot(figsize=(30,10))
    fig.set_xlabel('Time')
    fig.set_ylabel('Energy')
    fig.set_title('Demand over time with HVAC state')
    fig.get_figure().savefig('cumulative.png')

def demand_report():
    results = {}
    demand = get_demand()
    # total demand
    results['Demand Data'] = json.loads(demand.to_json())["1"]
    results['Total Demand'] = {'Amount': demand[1].sum(), 'Date': 'Last 30 days'}
    results['Max Inst Demand'] = {}
    results['Min Inst Demand'] = {}
    results['Max Inst Demand']['Amount'] = demand[1].max()
    results['Max Inst Demand']['Date'] = str(demand[1].argmax())
    results['Max Inst Demand']['Data'] = {k: data_hvaczone_day(k, demand[1].argmax()) for k in zones}
    results['Min Inst Demand']['Amount'] = demand[1].min()
    results['Min Inst Demand']['Date'] = str(demand[1].argmin())
    results['Min Inst Demand']['Data'] = {k: data_hvaczone_day(k, demand[1].argmax()) for k in zones}
    # get daily averages of demand
    daily = demand.resample('D',pd.np.sum)
    results['Max Daily Total Demand'] = {}
    results['Min Daily Total Demand'] = {}
    results['Max Daily Total Demand']['Amount'] = daily[1].max()
    results['Max Daily Total Demand']['Date'] = str(daily[1].argmax())
    results['Max Daily Total Demand']['Data'] = {k: data_hvaczone_day(k, daily[1].argmax()) for k in zones}
    results['Min Daily Total Demand']['Amount'] = daily[1].min()
    results['Min Daily Total Demand']['Date'] = str(daily[1].argmin())
    results['Max Daily Total Demand']['Data'] = {k: data_hvaczone_day(k, daily[1].argmin()) for k in zones}
    daily = demand.resample('D',pd.np.mean)
    results['Max Daily Avg Demand'] = {}
    results['Min Daily Avg Demand'] = {}
    results['Max Daily Avg Demand']['Amount'] = daily[1].max()
    results['Max Daily Avg Demand']['Date'] = str(daily[1].argmax())
    results['Max Daily Avg Demand']['Data'] = {k: data_hvaczone_day(k, daily[1].argmax()) for k in zones}
    results['Min Daily Avg Demand']['Amount'] = daily[1].min()
    results['Min Daily Avg Demand']['Date'] = str(daily[1].argmin())
    results['Max Daily Avg Demand']['Data'] = {k: data_hvaczone_day(k, daily[1].argmax()) for k in zones}

    return results

def hvac_report():
    results = {}
    hvacs = get_hvacstates()
    for zone,hvac in hvacs.iteritems():
        results[zone] = {}
        total_cooling = hvac[hvac[1] == 2].count()[1] * 5 # number of seconds
        total_heating = hvac[hvac[1] == 1].count()[1] * 5 # number of seconds
        total_off = hvac[hvac[1] == 0].count()[1] * 5 # number of seconds
        results[zone]['Total Cooling Time'] = str(datetime.timedelta(seconds = total_cooling))
        results[zone]['Total Heating Time'] = str(datetime.timedelta(seconds = total_heating))
        results[zone]['Total Off Time'] = str(datetime.timedelta(seconds = total_off))
    for zone,hvac in get_zonetemps().iteritems():
        results[zone]['Max Inst Temperature Amount'] = hvac[1].max()
        results[zone]['Max Inst Temperature Date'] = str(hvac[1].argmax())
        results[zone]['Min Inst Temperature Amount'] = hvac[1].min()
        results[zone]['Min Inst Temperature Date'] = str(hvac[1].argmin())
        daily = hvac.resample('D',pd.np.mean)
        results[zone]['Max Avg Temperature Amount'] = daily[1].max()
        results[zone]['Max Avg Temperature Date'] = str(daily[1].argmax())
        results[zone]['Min Avg Temperature Amount'] = daily[1].min()
        results[zone]['Min Avg Temperature Date'] = str(daily[1].argmin())
    return results

def data_hvaczone(zone):
    """
    For given HVACzone, get hvac_state, temp_cool, temp_heat and temp
    """
    hvac_state = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%hvac_state'".format(zone),start,end)
    temp_cool = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%temp_cool'".format(zone),start,end)
    temp_heat = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%temp_heat'".format(zone),start,end)
    temp = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%temp'".format(zone),start,end)

    return {'hvac_state': hvac_state.copy(), 'temp_cool': temp_cool.copy(), 'temp_heat': temp_heat.copy(), 'temp': temp.copy()}

def data_hvaczone_day(zone, day):
    """
    Gets hvac_state, temp_cool, temp_heat, temp for ZONE on a given day ([day] is a pandas Timestamp object)
    """
    start = int((datetime.datetime.combine(day.date(), datetime.datetime.min.time()) - datetime.datetime(1970,1,1)).total_seconds())
    end = start + 60*60*24
    hvac_state = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%hvac_state'".format(zone),start,end)
    temp_cool = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%temp_cool'".format(zone),start,end)
    temp_heat = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%temp_heat'".format(zone),start,end)
    temp = getdataasjson("Metadata/System = 'HVAC' and Metadata/HVACZone = '{0}' and Path like '%temp'".format(zone),start,end)

    return {'hvac_state': hvac_state.copy(), 'temp_cool': temp_cool.copy(), 'temp_heat': temp_heat.copy(), 'temp': temp.copy()}

def disaggregate():
    results = {}
    for zone, merge in resample_and_merge():
        merge = merge.dropna()
        idxs = group_contiguous(merge, 'state', 2)
        guesses = []
        for idx in idxs:
            mean_demand = merge.iloc[idx[1]:idx[2]]['demand'].mean()
            if not mean_demand > 0: continue # check for NaN and skip
            before_demand = merge.iloc[idx[0]]['demand']
            after_demand = merge.iloc[idx[3]]['demand']
            if idx[4]:
                base = min(after_demand, before_demand)
                diff = mean_demand - base
                guesses.append(diff)
        if len(guesses):
            results[zone] = sum(guesses) / float(len(guesses)) # use average
    return results

def save_as_json():
    d = {}
    d['demand'] = demand_report()
    d['hvac'] = hvac_report()
    #d['disaggregate'] = disaggregate()
    json.dump(d,open('report.json','w+'))

if __name__ == '__main__':
    #merge = resample_and_merge_cumulative()
    #merge = merge.dropna(how='any')
    #idxs = group_contiguous(merge, 'state', 0)
    #for idx in idxs:
    #    mean_demand = merge.iloc[idx[1]:idx[2]]['demand'].mean()
    #    before_demand = merge.iloc[idx[0]]['demand']
    #    after_demand = merge.iloc[idx[3]]['demand']
    #    print 'State: {0}, Mean during: {1}, Before: {2}, After: {3}, Samples: {4}'.format(idx[4], mean_demand, before_demand, after_demand, idx[2]-idx[1])
    save_as_json()
