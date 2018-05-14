"""
This uses the similarity-based approach to predict electrical load (without lights or HVAC)
for a given day using historical data. The similarity approach uses 30min-mean buckets of
historical data for the full building electrical meter;  it finds the 10 days with the lowest
mean-squared-error compared to the data gathered for the day to be predicted.

To get the load without lighting, we subtract the sum of the lighting consumption meters
(which we find using the Brick model).

To get the load without HVAC, we use the "max" bucket to estimate the state of a thermostat
for each 30min window, and then use estimates of load-while-heating and load-while-cooling
and subtact those from the full building meter.

@author: Gabe Fierro
"""

from xbos import get_client
from xbos.services.mdal import *
from xbos.services.hod import HodClient
import pandas as pd
import pytz
from sklearn.metrics import mean_squared_error
from dateutil import rrule
from datetime import datetime, timedelta

# data clients
mdal = MDALClient("xbos/mdal")
hod = HodClient("xbos/hod")

# temporal parameters
SITE = "ciee"

# Brick queries
building_meters_query = """SELECT ?meter ?meter_uuid FROM %s WHERE {
    ?meter rdf:type brick:Building_Electric_Meter .
    ?meter bf:uuid ?meter_uuid .
};"""
thermostat_state_query = """SELECT ?tstat ?status_uuid FROM %s WHERE {
    ?tstat rdf:type brick:Thermostat_Status .
    ?tstat bf:uuid ?status_uuid .
};"""
lighting_state_query = """SELECT ?lighting ?state_uuid FROM %s WHERE {
    ?light rdf:type brick:Lighting_State .
    ?light bf:uuid ?state_uuid
};"""
lighting_meter_query = """SELECT ?lighting ?meter_uuid FROM %s WHERE {
    ?meter rdf:type brick:Electric_Meter .
    ?lighting rdf:type brick:Lighting_System .
    ?lighting bf:hasPoint ?meter .
    ?meter bf:uuid ?meter_uuid
};"""

def predict_day(targetday="2018-02-01 00:00:00 PST", WINDOW="30m", N_DAYS=10):
    T0 = "2018-01-01 00:00:00 PST"
    day = datetime.strptime(targetday, "%Y-%m-%d %H:%M:%S %Z")
    day = pytz.timezone('US/Pacific').localize(day)
    T1 = (day - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")
    tomorrow = (day + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")

    today_start = targetday
    today_end = (day + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")

    # retrieve data
    building_meters_query_mdal = {
	"Composition": ["meter","tstat_state"],
	"Selectors": [MEAN, MAX],
	"Variables": [
	    {
		"Name": "meter",
		"Definition": building_meters_query % SITE,
		"Units": "kW"
	    },
	    {
		"Name": "tstat_state",
		"Definition": thermostat_state_query % SITE,
	    }
	    ],
	"Time": {
		"T0": T0, "T1": T1,
		"WindowSize": WINDOW,
		"Aligned": True,
	    }
    }
    resp = mdal.do_query(building_meters_query_mdal)
    df = resp['df']

    consumption_today_sofar = {
	"Composition": ["meter"], "Selectors": [MEAN],
	"Variables": [{
		"Name": "meter",
		"Definition": building_meters_query % SITE,
		"Units": "kW"
	    }],
	"Time": {
	    "T0": today_start,
	    "T1": today_end,
	    "WindowSize": WINDOW,
	    "Aligned": True,
	}
    }
    resp = mdal.do_query(consumption_today_sofar)
    sample = resp['df']

    lighting_meter_query_mdal = {
	"Composition": ["lighting"],
	"Selectors": [MEAN],
	"Variables": [
	    {
		"Name": "lighting",
		"Definition": lighting_meter_query % SITE,
		"Units": "kW"
	    },
	    ],
	"Time": {
		"T0": T0, "T1": T1,
		"WindowSize": WINDOW,
		"Aligned": True,
	    }
    }
    resp = mdal.do_query(lighting_meter_query_mdal, timeout=120)
    lighting_df = resp['df']

    # The first column of our DataFrame contains the average building meter data.  We want to 
    # subtract from that column the energy consumed when thermostats are in heating or cooling mode. 
    # If the thermostat mode column is 1, then the thermostat is heating. If it is 2, then the 
    # thermostat is cooling. We are fudging how to handle the 'statistical summary' of a thermostat 
    # state by using max(); more sophisticated methods may do a linear scale based on the mean value.

    # We use the following values for power consumed: heating (.3 kW) and cooling (5 kW)

    heating_consume = .3 # in kW
    cooling_consume = 5. # kW
    meter = df.columns[0]
    all_but_meter = df.columns[1:]

    # amount to subtract for heating, cooling
    # sum() works here because the output of the equality filter is boolean values (True is 1, False is 0)
    h = (df[all_but_meter] == 1).apply(sum, axis=1) * heating_consume
    c = (df[all_but_meter] == 2).apply(sum, axis=1) * cooling_consume

    meterdata = df[meter]  - h - c

    # do the same for lighting
    #meterdata = meterdata - (lighting_df.apply(sum, axis=1))

    # Similarity-based estimation implementation
    begin = meterdata.index[0].to_pydatetime()
    end = meterdata.index[-1].to_pydatetime()
    hop = rrule.DAILY
    hop_day = 1
    errors = []
    for dt in rrule.rrule(hop, dtstart=begin, until=end):
	# data for the current day
	day_meterdata = meterdata[dt:dt+timedelta(days=hop_day)]
	
	# avoids indexing errors by making sure the # of data points aligns
	num_sample = len(sample)
	num_meterdata = len(day_meterdata)
	num_use = min(num_sample, num_meterdata)
	today_data = sample.copy()[:num_use]
	use_meter = day_meterdata[:num_use]
	
	
	today_data.index = use_meter.index # move them onto the same day to aid subtraction
	sample_meter = today_data.columns[0]

        use_meter.fillna(0, inplace=True)
        today_data[sample_meter].fillna(0, inplace=True)
	
	# compare MSE error of today compared with the historical day
	mse = mean_squared_error(today_data[sample_meter], use_meter)
	errors.append(mse)

    d = pd.DataFrame(errors)

    # sort errors ascending and take first 10 values
    best_10_days = d.sort_values(0, ascending=True).head(N_DAYS)
    # use the index of the value to figure out how many days since the first date ("start", above)
    best_10_days_dates = [begin+timedelta(days=hop_day*x) for x in best_10_days.index]
    # grab the daily data for each of those days and put it into a new dataframe
    best_10_days_data = [df[meter][x:x+timedelta(days=hop_day)].values for x in best_10_days_dates]
    predictor_days_df = pd.DataFrame(best_10_days_data)

    predicted_day = predictor_days_df.mean(axis=0)
    predicted_day.index = pd.date_range(targetday, tomorrow, freq="30min")
    return predicted_day
