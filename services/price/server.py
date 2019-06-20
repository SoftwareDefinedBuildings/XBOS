from concurrent import futures
import datetime
import pytz
import time
import grpc
import logging
logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S', level=logging.DEBUG)
import price_pb2
import price_pb2_grpc
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar,USColumbusDay
import numpy as np
import pymortar
import requests
import csv
from rfc3339 import rfc3339
import os, sys
from pathlib import Path

import logging
import traceback

logging.basicConfig(format='%(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


PRICE_HOST_ADDRESS = os.environ["PRICE_HOST_ADDRESS"]
PRICE_DATA_PATH = Path(os.environ["PRICE_DATA_PATH"])

PGE_URL = os.environ["PGE_URL"]
PGE_WKDAY_MAX_TEMP = int(os.environ["PGE_WKDAY_MAX_TEMP"])
PGE_WKDAY_MIN_TEMP = int(os.environ["PGE_WKDAY_MIN_TEMP"])
PGE_WKEND_MAX_TEMP = int(os.environ["PGE_WKEND_MAX_TEMP"])
PGE_WKEND_MIN_TEMP = int(os.environ["PGE_WKEND_MIN_TEMP"])

SCE_URL = os.environ["SCE_URL"]

UNLIKELY = 0
POSSIBLE = 1
LIKELY = 2
CONFIRMED = 3

PGE_HOLIDAY_CAL = USFederalHolidayCalendar()
# Remove Columbus Day rule
if USColumbusDay in PGE_HOLIDAY_CAL.rules:
    PGE_HOLIDAY_CAL.rules.remove(USColumbusDay)


_ONE_DAY_IN_SECONDS = 60 * 60 * 24
UUID = {
    "PGE_PGEFLAT06_ENERGY":"5f8add28-9d7f-3e02-b428-bb32f241090d",
    "PGE_PGEA01_ENERGY":"6ec2b69f-ed98-3b58-b664-fedc3e0ebc3a",
    "PGE_PGEA06_ENERGY":"476c4dea-6ae7-3476-9b07-d3a932e48ffa",
    "PGE_PGEA10_ENERGY":"f1a7f547-896f-33fc-9fe3-f585495a6839",
    "PGE_PGEE19_ENERGY":"5a32eeeb-c404-3f90-9151-fa87d09cc924",
    "PGE_PGEE20_ENERGY":"679582c3-775d-304a-b36d-c4d8745d7e8e",
    "PGE_PGEFLAT06_DEMAND":"7776b145-e687-3d2b-9513-29ac9ef6c452",
    "PGE_PGEA01_DEMAND":"eebe1b61-fcf6-3944-8071-9abc9cb4ee95",
    "PGE_PGEA06_DEMAND":"a7096d20-9076-375a-b830-1101d1aeb248",
    "PGE_PGEA10_DEMAND":"7bef8016-fe56-3855-bb40-7ae22da1a600",
    "PGE_PGEE19_DEMAND":"cb59eab1-8f0a-3def-8c00-ea6bfd896dfb",
    "PGE_PGEE20_DEMAND":"8bf48154-debc-30d8-a130-edb4cbd0fa0c",
    "SCE_SCE08B_ENERGY" :"a94fba90-ac92-35a9-a18b-33673765ea21",
    "SCE_SCETGS3_ENERGY":"bea43675-6729-3623-a6c7-2d512cdb509e",
    "SCE_SCE08B_DEMAND" :"6ffda3c2-710c-3962-ac13-912d10e95bc0",
    "SCE_SCETGS3_DEMAND":"31e3e0e4-f319-390d-a015-cdd2bde0e8d0"
}

ALL_TARIFFS_UTILITIES = {
    "PGE":["PGEFLAT06","PGEA01","PGEA06","PGEA10","PGEE19","PGEE20"],
    "SCE":["SCE08B","SCETGS3"]
}

# TODO STORE AND UPDATE LIST SOMEWHERE THEN WE CAN GET HISTORICAL DR DATES
# LIST OF HISTORICAL EVENT DAYS FOR 2017 and 2018
# ,end_date,start_date,utility_id,date,utility
# 0,2017-06-16 23:00:00-08:00,2017-06-16 00:00:00-08:00,14328,2017-06-16,PGE
# 1,2017-06-19 23:00:00-08:00,2017-06-19 00:00:00-08:00,14328,2017-06-19,PGE
# 2,2017-06-20 23:00:00-08:00,2017-06-20 00:00:00-08:00,14328,2017-06-20,PGE
# 3,2017-06-22 23:00:00-08:00,2017-06-22 00:00:00-08:00,14328,2017-06-22,PGE
# 4,2017-06-23 23:00:00-08:00,2017-06-23 00:00:00-08:00,14328,2017-06-23,PGE
# 5,2017-07-07 23:00:00-08:00,2017-07-07 00:00:00-08:00,14328,2017-07-07,PGE
# 6,2017-07-27 23:00:00-08:00,2017-07-27 00:00:00-08:00,14328,2017-07-27,PGE
# 7,2017-07-31 23:00:00-08:00,2017-07-31 00:00:00-08:00,14328,2017-07-31,PGE
# 8,2017-08-01 23:00:00-08:00,2017-08-01 00:00:00-08:00,14328,2017-08-01,PGE
# 9,2017-08-02 23:00:00-08:00,2017-08-02 00:00:00-08:00,14328,2017-08-02,PGE
# 10,2017-08-28 23:00:00-08:00,2017-08-28 00:00:00-08:00,14328,2017-08-28,PGE
# 11,2017-08-29 23:00:00-08:00,2017-08-29 00:00:00-08:00,14328,2017-08-29,PGE
# 12,2017-08-31 23:00:00-08:00,2017-08-31 00:00:00-08:00,14328,2017-08-31,PGE
# 13,2017-09-01 23:00:00-08:00,2017-09-01 00:00:00-08:00,14328,2017-09-01,PGE
# 14,2017-09-02 23:00:00-08:00,2017-09-02 00:00:00-08:00,14328,2017-09-02,PGE
# 15,2017-06-19 23:00:00-08:00,2017-06-19 00:00:00-08:00,17609,2017-06-19,SCE
# 16,2017-06-20 23:00:00-08:00,2017-06-20 00:00:00-08:00,17609,2017-06-20,SCE
# 17,2017-07-06 23:00:00-08:00,2017-07-06 00:00:00-08:00,17609,2017-07-06,SCE
# 18,2017-07-07 23:00:00-08:00,2017-07-07 00:00:00-08:00,17609,2017-07-07,SCE
# 19,2017-07-27 23:00:00-08:00,2017-07-27 00:00:00-08:00,17609,2017-07-27,SCE
# 20,2017-07-31 23:00:00-08:00,2017-07-31 00:00:00-08:00,17609,2017-07-31,SCE
# 21,2017-08-01 23:00:00-08:00,2017-08-01 00:00:00-08:00,17609,2017-08-01,SCE
# 22,2017-08-28 23:00:00-08:00,2017-08-28 00:00:00-08:00,17609,2017-08-28,SCE
# 23,2017-08-29 23:00:00-08:00,2017-08-29 00:00:00-08:00,17609,2017-08-29,SCE
# 24,2017-08-31 23:00:00-08:00,2017-08-31 00:00:00-08:00,17609,2017-08-31,SCE
# 25,2017-09-05 23:00:00-08:00,2017-09-05 00:00:00-08:00,17609,2017-09-05,SCE
# 26,2017-09-12 23:00:00-08:00,2017-09-12 00:00:00-08:00,17609,2017-09-12,SCE
# 27,2018-06-12 23:00:00-08:00,2018-06-12 00:00:00-08:00,14328,2018-06-12,PGE
# 28,2018-06-13 23:00:00-08:00,2018-06-13 00:00:00-08:00,14328,2018-06-13,PGE
# 29,2018-07-10 23:00:00-08:00,2018-07-10 00:00:00-08:00,14328,2018-07-10,PGE
# 30,2018-07-16 23:00:00-08:00,2018-07-16 00:00:00-08:00,14328,2018-07-16,PGE
# 31,2018-07-17 23:00:00-08:00,2018-07-17 00:00:00-08:00,14328,2018-07-17,PGE
# 32,2018-07-19 23:00:00-08:00,2018-07-19 00:00:00-08:00,14328,2018-07-19,PGE
# 33,2018-07-24 23:00:00-08:00,2018-07-24 00:00:00-08:00,14328,2018-07-24,PGE
# 34,2018-07-25 23:00:00-08:00,2018-07-25 00:00:00-08:00,14328,2018-07-25,PGE
# 35,2018-07-27 23:00:00-08:00,2018-07-27 00:00:00-08:00,14328,2018-07-27,PGE
# 36,2018-07-06 23:00:00-08:00,2018-07-06 00:00:00-08:00,17609,2018-07-06,SCE
# 37,2018-07-09 23:00:00-08:00,2018-07-09 00:00:00-08:00,17609,2018-07-09,SCE
# 38,2018-07-10 23:00:00-08:00,2018-07-10 00:00:00-08:00,17609,2018-07-10,SCE
# 39,2018-07-17 23:00:00-08:00,2018-07-17 00:00:00-08:00,17609,2018-07-17,SCE
# 40,2018-07-18 23:00:00-08:00,2018-07-18 00:00:00-08:00,17609,2018-07-18,SCE
# 41,2018-08-01 23:00:00-08:00,2018-08-01 00:00:00-08:00,17609,2018-08-01,SCE
# 42,2018-08-02 23:00:00-08:00,2018-08-02 00:00:00-08:00,17609,2018-08-02,SCE
# 43,2018-08-06 23:00:00-08:00,2018-08-06 00:00:00-08:00,17609,2018-08-06,SCE
# 44,2018-08-07 23:00:00-08:00,2018-08-07 00:00:00-08:00,17609,2018-08-07,SCE
# 45,2018-08-09 23:00:00-08:00,2018-08-09 00:00:00-08:00,17609,2018-08-09,SCE
# 46,2018-09-28 23:00:00-08:00,2018-09-28 00:00:00-08:00,17609,2018-09-28,SCE
# 47,2018-10-18 23:00:00-08:00,2018-10-18 00:00:00-08:00,17609,2018-10-18,SCE



def get_dr_confirmed_pge():
    #TODO FIGURE OUT A WAY TO GET CONFIRMED DR EVENTS FOR PGE
    return price_pb2.DemandResponseReply(), None


# THIS FUNCTION FOLLOWS TO AN EXTENT THE FOLLOWING LOGIC:
# https://www.pge.com/resources/js/pge_five_day_forecast_par-pdp.js
def get_dr_forecast_pge():
    with requests.Session() as s:
        download = s.get(PGE_URL)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        statuses = []
        for i in range(0,10,2):
            dt = datetime.datetime.strptime(my_list[3][i+9], '%m/%d/%Y')
            dt = pytz.timezone('US/Pacific').localize(dt)
            temp = int(my_list[26][i+14])
            status = UNLIKELY
            if dt in PGE_HOLIDAY_CAL.holidays() or dt.weekday()>4:
                if temp>=PGE_WKEND_MAX_TEMP:
                    status=LIKELY
                elif temp>=PGE_WKEND_MIN_TEMP:
                    status=POSSIBLE
                else:
                    status=UNLIKELY
            else:
                if temp>=PGE_WKDAY_MAX_TEMP:
                    status=LIKELY
                elif temp>=PGE_WKDAY_MIN_TEMP:
                    status=POSSIBLE
                else:
                    status=UNLIKELY
            statuses.append(price_pb2.DemandResponsePoint(time=int(dt.timestamp() * 1e9),status=status))
        return price_pb2.DemandResponseReply(statuses=statuses),None

def get_dr_confirmed_sce():
    return price_pb2.DemandResponseReply(), None

    with requests.Session() as s:
        download = s.get(SCE_URL)
        decoded_content = download.content.decode('utf-8')
        df = pd.read_html(decoded_content)
        #     for item in df:
        #         print("------")
        #         print(item)
        #         print("------")
        #TODO FINISH THIS use df[1] or df[5] to get CONFIRMED CPP INCLUDING TODAY & TOMORROW
        return df[0]["Expected Pricing Category*"].to_dict()

def get_dr_forecast_sce():
    with requests.Session() as s:
        download = s.get(SCE_URL)
        decoded_content = download.content.decode('utf-8')
        df = pd.read_html(decoded_content)
        df[0]["Date of Usage"] = pd.to_datetime(df[0]["Date of Usage"]).dt.tz_localize(tz='US/Pacific')
        df[0].set_index("Date of Usage",inplace=True)
        df[0]["Expected Pricing Category*"].replace("EXTREMELY HOT SUMMER WEEKDAY",LIKELY,inplace=True)
        df[0]["Expected Pricing Category*"].replace("HOT SUMMER WEEKDAY",POSSIBLE,inplace=True)
        df[0]["Expected Pricing Category*"].replace("EXTREMELY HOT SUMMER WEEKDAY",POSSIBLE,inplace=True)
        df[0]["Expected Pricing Category*"].replace(regex='([a-zA-Z])',value=UNLIKELY,inplace=True)
        today = datetime.datetime.now()
        today = pytz.timezone('US/Pacific').localize(datetime.datetime(year=today.year, month=today.month, day=today.day, hour=0, minute=0))
        logging.info(today)
        if today in df[0].index:
            df[0] = df[0].drop(today, axis=0)
        # df[0] = df[0].drop(pytz.timezone('US/Pacific').localize(datetime.date.today()), axis=0)
        statuses = []
        for index, row in df[0].iterrows():
            statuses.append(price_pb2.DemandResponsePoint(time=int(index.timestamp()*1e9), status=row["Expected Pricing Category*"]))

        return price_pb2.DemandResponseReply(statuses=statuses),None

def get_dr_forecast(request):
    logging.info("received GetDemandResponseForecast request:%s",request.utility)
    # forecast is only for PGE PDP and SCE CPP
    if len(request.utility)==0 or request.utility.upper() not in ["PGE","SCE"]:
        return None, "Invalid request, only PGE or SCE utilities are supported"
    if request.utility.upper() == "SCE":
        return get_dr_forecast_sce()
    else:
        return get_dr_forecast_pge()

def get_dr_confirmed(request):
    logging.info("received GetDemandResponseConfirmed request:%s",request.utility)
    # forecast is only for PGE PDP and SCE CPP
    if len(request.utility)==0 or request.utility.upper() not in ["PGE","SCE"]:
        return None, "Invalid request, only PGE or SCE utilities are supported"
    if request.utility.upper() == "SCE":
        return get_dr_confirmed_sce()
    else:
        return get_dr_confirmed_pge()



def get_tariff_and_utility(request, df):
    """Returns tariff and utility for the specified building"""
    logging.info("received GetTariffAndUtility request:%s",request.building)

    building_df = df.loc[df["Building"] == request.building]

    if building_df.empty:
        return None, "invalid request, invalid building name"
        # return price_pb2.TariffUtilityReply(tariff="", utility=""), "empty data frame"

    utility, tariff = building_df["Utility"].item(), building_df["Tariff"].item()

    return price_pb2.TariffUtilityReply(tariff=tariff, utility=utility), None

def get_window_in_sec(s):
    """Returns number of seconds in a given duration or zero if it fails.
       Supported durations are seconds (s), minutes (m), hours (h), and days(d)."""
    seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        return int(float(s[:-1])) * seconds_per_unit[s[-1]]
    except:
        return 0

def get_from_csv(start, end, key, uuid, price_type,all_tariffs_utilities_dfs):
    tariff = key[key.index("_") + 1:key.rindex("_")]
    df = all_tariffs_utilities_dfs[tariff]

    prices = []
    utc_timestamps = []
    df = df[df.index >= pd.Timestamp(start)]
    df = df[df.index <= pd.Timestamp(end)]

    for index, row in df.iterrows():
        utc_timestamps.append(index)

        if price_type == "ENERGY":
            prices.append(round(row['customer_energy_charge']+row['pdp_non_event_energy_credit']+row['pdp_event_energy_charge'], 2))
        elif price_type == "DEMAND":
            prices.append(round(row['customer_demand_charge_season']+row['pdp_non_event_demand_credit']+row['customer_demand_charge_tou'], 2))

    return pd.DataFrame(data=prices, columns=[uuid], index=utc_timestamps)


def get_from_pymortar(start, end, uuid, pymortar_client):

    price_stream = pymortar.DataFrame(
        name="price_data",
        uuids=[uuid],
        aggregation=pymortar.MEAN,
        window="1h"
    )

    price_time_params = pymortar.TimeParams(
        start=rfc3339(start),
        end=rfc3339(end),
    )

    price_request = pymortar.FetchRequest(
        sites=[""],
        dataFrames=[
            price_stream
        ],
        time=price_time_params
    )

    return pymortar_client.fetch(price_request)["price_data"]

def get_price(request, pymortar_client, all_tariffs_utilities_dfs):
    """Returns prices for a given request or None."""
    logging.info("received GetPrice request:%s %s %s %s %s %s",request.utility,request.tariff,request.price_type,request.start,request.end,request.window)
    if request.price_type.upper() == "ENERGY":
        unit = "$/kWh"
    elif request.price_type.upper() == "DEMAND":
        unit = "$/kW"
    else:
        return None, "invalid request, invalid price_type"
    duration = get_window_in_sec(request.window)
    request_length = [len(request.utility),len(request.tariff),request.start,request.end,duration]
    if any(v == 0 for v in request_length):
        return None, "invalid request, empty params"
    if duration <= 0:
        return None, "invalid request, window is negative or zero"
    if request.start <0 or request.end <0:
        return None, "invalid request, negative dates"
    if request.end > int((time.time()+_ONE_DAY_IN_SECONDS)*1e9):
        return None, "invalid request, end date is too far in the future, max is 24h from now"
    if request.start >= request.end:
        return None, "invalid request, start date is equal or after end date."
    if request.start + (duration * 1e9) > request.end:
        return None, "invalid request, start date + window is greater than end date"

    key = request.utility.upper()+"_"+request.tariff.upper()+"_"+request.price_type.upper()
    if key in UUID:
        uuid = UUID.get(key)
    else:
        return None, "invalid request, no uuid for given utility,tariff,price_type"

    # raw price data is stored at 1h frequency
    end = request.end
    if duration < 3600:
        # if request.start-end < 1h, return at least 1 hr
        if request.end < request.start + 36e11:
            end = request.start + 36e11
        # if request.end does not end on the hour and duration adds up to an hour, request an extra hour
        # e.g., asking for 4:10 returns up to 3:00, then ask for 5:00 to force it to return 4:00
        elif request.end/1e9%3600!=0:
            end = request.end + 36e11
    #Aligned returns invalid (next) price (we request the equivalent of RAW)

    csv_end_date = pytz.timezone('US/Pacific').localize(datetime.datetime(year=2019, month=4, day=16, hour=0, minute=0,second=0)).astimezone(pytz.utc)
    datetime_end = datetime.datetime.utcfromtimestamp(int(end / 1e9)).replace(tzinfo=pytz.utc)
    datetime_start = datetime.datetime.utcfromtimestamp(int(request.start/1e9- request.start/1e9%3600)).replace(tzinfo=pytz.utc)
    datetime_req_start = datetime.datetime.utcfromtimestamp(int(request.start/1e9)).replace(tzinfo=pytz.utc)

    if datetime_end <= csv_end_date:
        df = get_from_csv(datetime_start, datetime_end, key, uuid, request.price_type.upper(),all_tariffs_utilities_dfs)
    elif datetime_start >= csv_end_date:
        df = get_from_pymortar(datetime_start, datetime_end, uuid, pymortar_client)
    elif datetime_start < csv_end_date and datetime_end > csv_end_date:
        df_csv = get_from_csv(datetime_start, csv_end_date, key, uuid, request.price_type.upper(),all_tariffs_utilities_dfs)
        df_pymortar = get_from_pymortar(csv_end_date + datetime.timedelta(hours=1), datetime_end, uuid, pymortar_client)
        df = pd.concat([df_csv, df_pymortar])

    if df is None:
        return [price_pb2.PricePoint()], "did not fetch data"
        # return price_pb2.PriceReply(prices=[]), "did not fetch data"
    if df.empty:
        return [price_pb2.PricePoint()], "empty data frame"
        # return price_pb2.PriceReply(prices=[]), "empty data frame"
    df = df.dropna()
    if df.empty:
        return [price_pb2.PricePoint()], "empty data frame"
        # return price_pb2.PriceReply(prices=[]), "empty data frame"
    df = df.reset_index().drop_duplicates(subset='index', keep='first').set_index('index')
    interpolated_df = smart_resample(df, datetime_req_start, datetime_end, duration, "ffill")
    prices = []
    for index, row in interpolated_df.iterrows():
        prices.append(price_pb2.PricePoint(time=int(index.timestamp() * 1e9),price=row[uuid],unit=unit,window=request.window))

    # return price_pb2.PriceReply(prices=prices), None
    return prices, None

def smart_resample(data, start, end, window, method):
    """
    Groups data into intervals according to the method used.
    Returns data indexed with start to end in frequency of interval minutes.
    :param data: pd.series/pd.df has to have time series index which can contain a span from start to end. Timezone aware.
    :param start: the start of the data we want. Timezone aware
    :param end: the end of the data we want (not inclusive). Timezone aware
    :param window: (int seconds) interval length in which to split data.
    :param method: (optional string) How to fill nan values. Usually use pad (forward fill for setpoints) and
                            use "interpolate" for approximate linear processes (like outside temperature. For inside
                            temperature we would need an accurate thermal model.)
    :return: data with index of pd.date_range(start, end, interval). Returned in timezone of start.
    NOTE: - If (end - start) not a multiple of interval, then we choose end = start + (end - start)//inteval * interval.
                But the new end will not be inclusive.
          - If end is beyond the end of the data, it will assume that the last value has been constant until the
              given end.
    """
    end = end.astimezone(start.tzinfo)
    data = data.tz_convert(start.tzinfo)


    # make sure that the start and end dates are valid.
    data = data.sort_index()
    if not start <= end:
        raise Exception("Start is after End date.")
    if not start >= data.index[0]:
        raise Exception("Resample start date is further back than data start date -- can not resample.")
    if not window > 0:
        raise Exception("Interval has to be larger than 0.")

    # add date_range and fill nan's through the given method.
    date_range = pd.date_range(start, end, freq=str(window) + "S")
    end = date_range[-1]  # gets the right end.

    # Raise warning if we don't have enough data.
    if end - datetime.timedelta(seconds=window) > data.index[-1]:
        logging.warning("Warning: the given end is more than one interval after the last datapoint in the given data. %s minutes after end of data."
              % str((end - data.index[-1]).total_seconds()/60.))

    new_index = date_range.union(data.index).tz_convert(date_range.tzinfo)
    data_with_index = data.reindex(new_index)

    if method == "interpolate":
        data = data_with_index.interpolate("time")
    elif method in ["pad", "ffill"]:
        data = data_with_index.fillna(method=method)
    else:
        raise Exception("Incorrect method for filling nan values given.")

    data = data.loc[start: end]  # While we return data not inclusive, we need last datapoint for weighted average.

    def weighted_average_constant(datapoint, window):
        """Takes time weighted average of data frame. Each datapoint is weighted from its start time to the next
        datapoints start time.
        :param datapoint: pd.df/pd.series. index includes the start of the interval and all data is between start and start + interval.
        :param window: int seconds.
        :returns the value in the dataframe weighted by the time duration."""
        datapoint = datapoint.sort_index()
        temp_index = np.array(list(datapoint.index) + [datapoint.index[0] + datetime.timedelta(seconds=window)])
        diffs = temp_index[1:] - temp_index[:-1]
        weights = np.array([d.total_seconds() for d in diffs]) / float(window)
        assert 0.99 < sum(weights) < 1.01  # account for tiny precision errors.
        if isinstance(datapoint, pd.DataFrame):
            return pd.DataFrame(index=[datapoint.index[0]], columns=datapoint.columns, data=[datapoint.values.T.dot(weights)])
        else:
            return pd.Series(index=[datapoint.index[0]], data=datapoint.values.dot(weights))

    def weighted_average_linear(datapoint, window, full_data):
        """Takes time weighted average of data frame. Each datapoint is weighted from its start time to the next
        datapoints start time.
        :param datapoint: pd.df/pd.series. index includes the start of the interval and all data is between start and start + interval.
        :param window: int seconds.
        :returns the value in the dataframe weighted by the time duration."""
        datapoint = datapoint.sort_index()
        temp_index = np.array(list(datapoint.index) + [datapoint.index[0] + datetime.timedelta(seconds=window)])

        if isinstance(datapoint, pd.DataFrame):
            temp_values = np.array(
                list(datapoint.values) + [full_data.loc[temp_index[-1]].values])
        else:
            temp_values = np.array(list(datapoint.values) + [full_data.loc[temp_index[-1]]])

        new_values = []
        for i in range(0, len(temp_values)-1):
            new_values.append((temp_values[i+1] + temp_values[i])/2.)

        new_values = np.array(new_values)
        diffs = temp_index[1:] - temp_index[:-1]
        weights = np.array([d.total_seconds() for d in diffs]) / float(window)

        assert 0.99 < sum(weights) < 1.01  # account for tiny precision errors.
        if isinstance(datapoint, pd.DataFrame):
            return pd.DataFrame(index=[datapoint.index[0]], columns=datapoint.columns, data=[new_values.T.dot(weights)])
        else:
            return pd.Series(index=[datapoint.index[0]], data=new_values.dot(weights))

    if method == "interpolate":
        # take weighted average and groupby datapoints which are in the same interval.
        data_grouped = data.iloc[:-1].groupby(by=lambda x: (x - start).total_seconds() // window, group_keys=False).apply(func=lambda x: weighted_average_linear(x, window, data))
    else:
        data_grouped = data.iloc[:-1].groupby(by=lambda x: (x - start).total_seconds() // window, group_keys=False).apply(func=lambda x: weighted_average_constant(x, window))

    return data_grouped


class PriceServicer(price_pb2_grpc.PriceServicer):
    def __init__(self):
        self.pymortar_client = pymortar.Client()

        price_path = PRICE_DATA_PATH / "price-mapping.csv"
        if not os.path.isfile(str(price_path)):
            logging.critical("Error: could not find file at: %s" , str(price_path))
            sys.exit()

        self.price_mapping = pd.read_csv(str(price_path))
        tariffs_utilities = []
        self.all_tariffs_utilities_dfs = {}
        for utility, tariffs in ALL_TARIFFS_UTILITIES.items():
            for tariff in tariffs:
                tariffs_utilities.append(price_pb2.TariffUtilityReply(tariff=tariff, utility=utility))
                df = pd.read_csv(PRICE_DATA_PATH / ("prices_01012017_040172019/" + tariff + ".csv"), index_col=[0], parse_dates=False)
                df = df.fillna(0)
                df.index = pd.to_datetime(df.index)
                df = df.tz_localize("US/Pacific",nonexistent='shift_forward',ambiguous=False).tz_convert(pytz.utc)
                self.all_tariffs_utilities_dfs[tariff]= df
        self.all_tariffs_utilities = price_pb2.AllTariffUtilityReply(tariffs_utilities=tariffs_utilities)

    def GetPrice(self, request, context):
        try:
            prices,error = get_price(request,self.pymortar_client,self.all_tariffs_utilities_dfs)
            if prices is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return price_pb2.PricePoint()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            for price in prices:
                yield price
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return price_pb2.PricePoint()

    def GetTariffAndUtility(self, request, context):
        try:
            tariff_utility_reply,error = get_tariff_and_utility(request, self.price_mapping)
            if tariff_utility_reply is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return price_pb2.TariffUtilityReply()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return tariff_utility_reply
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return price_pb2.TariffUtilityReply()

    def GetDemandResponseForecast(self, request, context):
        try:
            dr_response,error = get_dr_forecast(request)
            if dr_response is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return price_pb2.DemandResponseReply()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return dr_response
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return price_pb2.DemandResponseReply()

    def GetDemandResponseConfirmed(self, request, context):
        try:
            dr_response,error = get_dr_confirmed(request)
            if dr_response is None:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(error)
                return price_pb2.DemandResponseReply()
            elif error is not None:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(error)
            return dr_response
        except Exception:
            tb = traceback.format_exc()
            logging.error(tb)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(tb)
            return price_pb2.DemandResponseReply()

    def GetAllTariffsAndUtilities(self,request,context):
        logging.info("received GetAllTariffsAndUtilities request")
        return self.all_tariffs_utilities

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    price_pb2_grpc.add_PriceServicer_to_server(PriceServicer(), server)
    server.add_insecure_port(PRICE_HOST_ADDRESS)
    logging.info("Serving on {0} with data path {1}".format(PRICE_HOST_ADDRESS, PRICE_DATA_PATH))
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
