import pandas as pd
import pytz
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar
import time
import datetime
import enum
import matplotlib.pyplot as plt
import matplotlib

def _select_demand(data): #and Temp
    # get only demand
    demand = data.filter(regex="demand").resample("15min").sum()
    temperature=data.filter(regex="IAT").resample("15min").mean()  ## change to "1h" for 1 hour pivots
    heating=data.filter(regex="Heating").resample("15min").mean()  # NOTE: Means again ?
    cooling=data.filter(regex="Cooling").resample("15min").mean()
    
    return demand, temperature, heating, cooling 

def _create_pivot(data, freq="15min"):
    
    if freq=="15min":
        data["date"] = data.index.date
        data["combined"]=data.index.hour+(data.index.minute*(1.0/60.0))
        #data_pivot=data.groupby(data["combined"])#.mean()[data.columns[0]]
        data_pivot = data.set_index(["date","combined"]).unstack()
        # remove double index
        data_pivot.columns = data_pivot.columns.droplevel(0)
        
    elif freq=="1h":
        # add date and hour for new index                          
        data["date"] = data.index.date
        data["hour"] = data.index.hour

        # create pivot
        data_pivot = data.set_index(["date","hour"]).unstack()
        # remove double index
        data_pivot.columns = data_pivot.columns.droplevel(0)

    return data_pivot

def _remove_event_day(data, event_day):
    '''
    data: pandas df indexed by timestamp
    event_day: pandas timestamp
    '''
    try:
        data = data[~(data.index.date == event_day.date())]
        return data
    except:
        return data

def _remove_event_days(data, event_days): 
    '''
    data: pandas df indexed by timestamp
    event_days: list of pandas timestamps
    '''
    for event_day in event_days:
        try:
            data = data[~(data.index.date == event_day.date())]
        except:
            pass
    return data

def _remove_WE_holidays_NaN(data):
    
    cal = calendar()
    start = datetime.datetime.strftime(data.index.min(),"%Y-%m-%d")
    end =datetime.datetime.strftime(data.index.max(),"%Y-%m-%d")
    hol_cal = cal.holidays(start=start, end=end)
    
    data = data.dropna(how='any') # remove if has any NaN for any hour
    
    no_hol = ~data.index.isin(hol_cal) # remove if it is a national holiday
    no_WE = ~((data.index.weekday == 5) | (data.index.weekday == 6)) # remove if WE
    
    return data[no_WE & no_hol]

def _get_last_Y_days(data, Y=10):
    
    try:
        data = data.sort_index(ascending=False).iloc[0:Y,:]
        return data
    except:
        print("data available only for {} days".format(data.shape[0]))
        return data
    
def _get_X_in_Y(data, X=None, event_start_h=14, event_end_h=18, include_last=False):
    
    if not X:
        X=data.shape[0]
    
    cols = range(event_start_h, event_end_h+include_last*1)
    sorted_days = data.iloc[:, cols].sum(axis=1).sort_values(ascending=False)
    x_days = data.iloc[:, cols].sum(axis=1).sort_values(ascending=False)[0:X].index
    
    #print ('get x in y', data[data.index.isin(x_days)] )
    return data[data.index.isin(x_days)], x_days

def _get_adj_ratio(data, 
                    event_data,
                    event_start_h=12,
                    min_ratio=1.0, 
                    max_ratio=1.2,):
    
    # this is hardcoded, we may want to do it in a more flexible way
    # strategy: 4 hours before the event, take the first 3 and average them
    pre_event_period_start = event_start_h - 4
    cols = range(pre_event_period_start, event_start_h - 1) 
    
    try:
        ratio = event_data[cols].mean().mean()/data[cols].mean().mean()
    except:
        ratio=1
    
    return ratio

def get_X_in_Y_baseline(data,
                        event_day,
                        X=3, 
                        Y=10, 
                        event_start_h=12,
                        event_end_h=18,
                        include_last=False,
                        adj_ratio=True,
                        min_ratio=1.0, 
                        max_ratio=1.2,
                        sampling="quarterly",
                        past_event_days=None,
                        max_day=None):
    '''
    X, Y 3 of 10: 
    
    '''
    event_data= data[data.index.date == event_day.date()]
    
    data = _remove_event_day(data, event_day)
    if past_event_days:
        data = _remove_event_days(data, past_event_days)
    if max_day:
        data = data[data.index.date == max_day.date()]
    data = _remove_WE_holidays_NaN(data)
    data = _get_last_Y_days(data, Y)
    days = data.index
    data, x_days = _get_X_in_Y(data, 
                       X=X, 
                       event_start_h=event_start_h, 
                       event_end_h=event_end_h, 
                       include_last=include_last)
    if adj_ratio:
    
        ratio = _get_adj_ratio(data, event_data, 
                               event_start_h=event_start_h,
                               min_ratio=min_ratio, 
                               max_ratio=max_ratio)
    else:
        ratio = 1
    ratio = 1 #TODO: ratio was causing NaNs
    data = (data.mean()*ratio).to_frame() # baseline is the average of the days selected
    data.columns = ["baseline"]
    return data, days, event_data.T, x_days

def make_baseline(x_days, event_day, pivot, name="Temperature", freq="15min"):
    baseline=pivot[pivot.index.isin(x_days)].mean(axis=0)
    baseline_df=baseline.to_frame(name)
    if freq=="15min":
        baseline_df=create_timeseries(baseline_df, event_day)
    return baseline_df

def create_timeseries(df, event_day):
    col=[]
    df.columns=['demand']
    for i in df.index:
        hours=int(i)//1
        minutes=(i%1)*60
        col.append(event_day+pd.Timedelta(hours=hours, minutes=minutes))
    df["Time"]=col

    adj_df=df.set_index(["Time"])
    df=adj_df[adj_df.columns[0]]
    return df