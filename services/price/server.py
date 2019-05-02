from concurrent import futures
import datetime
import pytz
import time
import grpc
import price_pb2
import price_pb2_grpc
import pandas as pd
import numpy as np
import pymortar
from rfc3339 import rfc3339
import os, sys
from pathlib import Path

PRICE_HOST_ADDRESS = os.environ["PRICE_HOST_ADDRESS"]
PRICE_DATA_PATH = Path(os.environ["PRICE_DATA_PATH"])

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


def get_tariff_and_utility(request, df):
    """Returns tariff and utility for the specified building"""

    building_df = df.loc[df["Building"] == request.building]

    if building_df.empty:
        return price_pb2.TariffUtilityReply(tariff="", utility=""), "empty data frame"

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
    print("received request:",request.utility,request.tariff,request.price_type,request.start,request.end,request.window)
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
        return price_pb2.PriceReply(prices=[]), "did not fetch data"
    if df.empty:
        return price_pb2.PriceReply(prices=[]), "empty data frame"
    df = df.dropna()
    if df.empty:
        return price_pb2.PriceReply(prices=[]), "empty data frame"
    interpolated_df = smart_resample(df, datetime_req_start, datetime_end, duration, "ffill")
    prices = []
    for index, row in interpolated_df.iterrows():
        prices.append(price_pb2.PricePoint(time=int(index.timestamp() * 1e9),price=row[uuid],unit=unit,window=request.window))

    return price_pb2.PriceReply(prices=prices), None

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
    try:
         end = end.astimezone(start.tzinfo)
         data = data.tz_convert(start.tzinfo)
    except:
         raise Exception("Start, End, Data need to be timezone aware.")


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
        print("Warning: the given end is more than one interval after the last datapoint in the given data. %s minutes after end of data."
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
            print("Error: could not find file at: " + str(price_path))
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
                df = df.tz_localize("US/Pacific",nonexistent='shift_forward' ,ambiguous=False).tz_convert(pytz.utc)
                self.all_tariffs_utilities_dfs[tariff]= df
        self.all_tariffs_utilities = price_pb2.AllTariffUtilityReply(tariffs_utilities=tariffs_utilities)

    def GetPrice(self, request, context):
        prices,error = get_price(request,self.pymortar_client,self.all_tariffs_utilities_dfs)
        if prices is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return price_pb2.PriceReply()
        elif error is not None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(error)
            return prices

        return prices

    def GetTariffAndUtility(self, request, context):
        tariff_utility_reply,error = get_tariff_and_utility(request, self.price_mapping)
        if tariff_utility_reply is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return price_pb2.TariffUtilityReply()
        elif error is not None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(error)
            return tariff_utility_reply

        return tariff_utility_reply

    def GetAllTariffsAndUtilities(self,request,context):
        return self.all_tariffs_utilities

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    price_pb2_grpc.add_PriceServicer_to_server(PriceServicer(), server)
    server.add_insecure_port(PRICE_HOST_ADDRESS)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
