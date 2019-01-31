from get_greenbutton_id import get_greenbutton_id
from event_table import event_table
from random import shuffle
from calc_price import *
import pandas as pd
import math
import os


def add_days(dt, days):
    date_time = (pd.to_datetime(dt) + pd.to_timedelta(days, unit='day'))
    result = str(date_time.date()) + 'T00:00:00Z'
    return result

def agg_tbl(table, event_start_hr, event_end_hr, tariff_opts):
    date = str(table.index[0].date())
    energy_baseline = power_15min_to_hourly_energy(table['baseline-demand'])
    energy_event = power_15min_to_hourly_energy(table['event-demand'])
    full_day_baseline = sum(energy_baseline)
    full_day_event = sum(energy_event)
    start = pd.to_datetime(date) + pd.Timedelta(event_start_hr, 'h')
    end = pd.to_datetime(date) + pd.Timedelta(event_end_hr, 'h')
    window_baseline = sum(energy_baseline[(energy_baseline.index >= start) & (energy_baseline.index <= end)])
    window_event = sum(energy_event[(energy_event.index >= start) & (energy_event.index <= end)])
    baseline_cost = calc_total_price(table['baseline-demand'], tariff_opts, table['event-demand'].index[0], table['event-demand'].index[-1])
    print('WINDOW BASELINE')
    print(window_baseline)
    event_cost = calc_total_price(table['event-demand'], tariff_opts, table['event-demand'].index[0], table['event-demand'].index[-1])
    event_peak_temp = max(table['event-weather'])
    baseline_peak_temp = max(table['baseline-weather'])
    max_demand_baseline = max(table['baseline-demand'])
    max_demand_event = max(table['event-demand'])
    return {
        'date': date,
        'baseline_full': full_day_baseline,
        'event_full': full_day_event,
        'baseline_window': window_baseline,
        'event_window': window_event,
        'baseline_peak_demand': max_demand_baseline,
        'event_peak_demand': max_demand_event,
        'baseline_cost': baseline_cost,
        'event_cost': event_cost,
        'event_peak_temp': event_peak_temp,
        'baseline_peak_temp': baseline_peak_temp
    }

def main(sites):
    all_events_dict = {}
    for site in sites:
        tarrifs = pd.read_csv('tariffs.csv', index_col='meter_id')
        events = pd.read_json('pricing/openei_tariff/PDP_events.json')
        meter_id = get_greenbutton_id(site, "2018-01-01T10:00:00-07:00", "2018-08-12T10:00:00-07:00")[0]
        tariff = tarrifs.loc[meter_id]
        utility_events = events[events['utility_id'] == tariff.utility_id]
        tables = utility_events.apply(lambda r: event_table(site, r['start_date'][:-6], add_days(r['start_date'], -40), add_days(r['start_date'], 40), max_baseline=True, offset=2), axis=1)
        dfs = [t['df'] for t in tables]
        outdir = './15min_interval/' + site 
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        for i in range(len(dfs)):
            df = dfs[i]
            date = utility_events['start_date'].iloc[i]
            df.to_csv(outdir + '/' + date[0:10] + '.csv')
        tariff = dict(tariff)
        # may have to change the line above
        if (not type(tariff['distrib_level_of_interest']) == str) and math.isnan(tariff['distrib_level_of_interest']):
            tariff['distrib_level_of_interest'] = None
        tariff['utility_id'] = str(tariff['utility_id'])
        all_events = [agg_tbl(df, 14, 18, tariff) for df in dfs]
        all_events = pd.DataFrame(all_events)[[
                'date',
                'baseline_full',
                'event_full',
                'baseline_window',
                'event_window',
                'baseline_peak_demand',
                'event_peak_demand',
                'baseline_cost',
                'event_cost',
                'event_peak_temp',
                'baseline_peak_temp',
            ]]
        all_events['savings'] = all_events['baseline_cost'] - all_events['event_cost']
        all_events['event_energy_savings'] = all_events['baseline_window'] - all_events['event_window']
        all_events_dict[site] = all_events
        all_events.to_csv('./daily/' + site + '.csv')
    return all_events_dict

from sites import sites
main(sites)


