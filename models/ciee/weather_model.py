from xbos import get_client
from xbos.services.mdal import *
from xbos.services.hod import HodClient
import pandas as pd
import pytz
from sklearn.metrics import mean_squared_error
from dateutil import rrule
from datetime import datetime, timedelta

# data clients
mdal = BOSSWAVEMDALClient("xbos/mdal")
hod = HodClient("xbos/hod")

# temporal parameters
SITE = "ciee"

def predict_day(targetday="2018-01-30 00:00:00 PST", WINDOW="30m", N_DAYS=10):
    T0 = "2017-09-18 00:00:00 PST"
    day = datetime.strptime(targetday, "%Y-%m-%d %H:%M:%S %Z")
    day = pytz.timezone('US/Pacific').localize(day)
    T1 = (day - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")
    tomorrow = (day + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")

    today_start = targetday
    today_end = (day + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %Z")
    print today_start, today_end

    # retrieve data
    weather_query = {
	"Composition": ["1c467b79-b314-3c1e-83e6-ea5e7048c37b"],
        "Variables": [],
	"Selectors": [MEAN],
	"Time": {
		"T0": T0, "T1": T1,
		"WindowSize": WINDOW,
		"Aligned": True,
	    }
    }
    resp = mdal.do_query(weather_query)
    df = resp['df']

    weather_today_sofar = {
	"Composition": ["1c467b79-b314-3c1e-83e6-ea5e7048c37b"],
        "Variables": [],
	"Selectors": [MEAN],
	"Time": {
	    "T0": today_start,
	    "T1": today_end,
	    "WindowSize": WINDOW,
	    "Aligned": True,
	}
    }
    resp = mdal.do_query(weather_today_sofar)
    sample = resp['df']

    # Similarity-based estimation implementation
    begin = df.index[0].to_pydatetime()
    #  convert to midnight of the next day
    begin = datetime(begin.year,begin.month,begin.day, tzinfo=begin.tzinfo) + timedelta(days=1)
    end = df.index[-1].to_pydatetime()
    # convert to midnight of previous day
    end = datetime(end.year, end.month, end.day, tzinfo=end.tzinfo)
    weather = df.columns[0]
    hop = rrule.DAILY
    hop_day = 1
    errors = []
    for dt in rrule.rrule(hop, dtstart=begin, until=end):
	# data for the current day
	day_weatherdata = df[dt:dt+timedelta(days=hop_day)]
	
	# avoids indexing errors by making sure the # of data points aligns
	num_sample = len(sample)
	num_weatherdata = len(day_weatherdata)
	num_use = min(num_sample, num_weatherdata)
	today_data = sample.copy()[:num_use]
	use_weather = day_weatherdata[:num_use]
	
	
	today_data.index = use_weather.index # move them onto the same day to aid subtraction
	sample_weather = today_data.columns[0]
	
	# compare MSE error of today compared with the historical day
	mse = mean_squared_error(today_data[sample_weather], use_weather)
	errors.append(mse)

    d = pd.DataFrame(errors)

    # sort errors ascending and take first 10 values
    best_10_days = d.sort_values(0, ascending=True).head(N_DAYS)
    # use the index of the value to figure out how many days since the first date ("start", above)
    best_10_days_dates = [begin+timedelta(days=hop_day*x) for x in best_10_days.index]
    # grab the daily data for each of those days and put it into a new dataframe
    best_10_days_data = [df[weather][x:x+timedelta(days=hop_day)].values for x in best_10_days_dates]
    predictor_days_df = pd.DataFrame(best_10_days_data)

    predicted_day = predictor_days_df.mean(axis=0)
    predicted_day.index = pd.date_range(targetday, tomorrow, freq="30min")
    return predicted_day

if __name__ == '__main__':
    print predict_day("2017-10-06 00:00:00 PST")
