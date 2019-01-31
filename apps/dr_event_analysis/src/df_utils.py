import pandas as pd
import pytz
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
import time
import datetime
import enum
from collect import get_weather_power_tstat
import matplotlib.pyplot as plt
import matplotlib

def _utc_to_local(data, local_zone="America/Los_Angeles"):

    try:
         data.index = data.index.tz_localize(local_zone)
    except(TypeError):
         data.index = data.index.tz_convert(local_zone) 
    # accounts for localtime shift
    # Gets rid of extra offset information so can compare with csv data
    # to account for dst
    data.index = data.index.tz_localize(None)
    return data
    
def _resample_at_Nmin(data,Nmin="15min",): 
    data = data.resample(Nmin).mean() # NOTE: had to change to how='mean'
    return data

def process_df(df, Nmin="15min", local_zone="America/Los_Angeles"):
    data = df
    data.index = pd.to_datetime(data.index)
    data.index.name = "datetime"
    data = _utc_to_local(data)
    data = _resample_at_Nmin(data,Nmin)
    return data

def _configure_MDAL_df(site, data, power_15min, meter_id = None):
    ''' 
    data: {
        'weather': resp_weather,
        'power': resp_power,
        'temperature': resp_temp, 
        'heat setpoint': resp_hsp,
        'cool setpoint': resp_csp
    }
    '''
    if meter_id != None:
        meter = meter_id
    else:
        meter=site_map.loc[site, 'Green_Button_Meter']
    power=power_15min[meter]
    temp_df = pd.DataFrame(data['temperature'].df.mean(axis=1),
            columns=['IAT_z0'])
    hsp_df = pd.DataFrame(data['heat setpoint'].df.mean(axis=1),
            columns=['heat_setpoint_z0'])
    csp_df = pd.DataFrame(data['cool setpoint'].df.mean(axis=1),
            columns=['cool_setpoint_z0'])
    tstat_data = temp_df.merge(hsp_df, left_index=True, right_index=True).merge(csp_df, left_index=True, right_index=True)
    df_tstat=process_df(tstat_data)
    df_tstat.columns = ['IAT_z0', 'heat_setpoint_z0', 'cool_setpoint_z0'] #TODO: Actually fix this
    df = df_tstat.join(power)[['heat_setpoint_z0', 'cool_setpoint_z0', 'IAT_z0', meter]]
    df.columns=['Heating', 'Cooling', 'IAT', 'demand']
    return df, site