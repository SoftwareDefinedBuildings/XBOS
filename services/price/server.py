from concurrent import futures
import time
import grpc
import price_pb2
import price_pb2_grpc
import pandas as pd
import pymortar
from rfc3339 import rfc3339
import os, sys

PRICE_HOST_ADDRESS = os.environ["PRICE_HOST_ADDRESS"]

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
UUID = {
    "PGE_FLAT06_ENERGY":"5f8add28-9d7f-3e02-b428-bb32f241090d",
    "PGE_PGEA01_ENERGY":"6ec2b69f-ed98-3b58-b664-fedc3e0ebc3a",
    "PGE_PGEA06_ENERGY":"476c4dea-6ae7-3476-9b07-d3a932e48ffa",
    "PGE_PGEA10_ENERGY":"f1a7f547-896f-33fc-9fe3-f585495a6839",
    "PGE_PGEE19_ENERGY":"5a32eeeb-c404-3f90-9151-fa87d09cc924",
    "PGE_PGEE20_ENERGY":"679582c3-775d-304a-b36d-c4d8745d7e8e",
    "PGE_FLAT06_DEMAND":"7776b145-e687-3d2b-9513-29ac9ef6c452",
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

def get_price_for_interval(df,t,uuid,duration):
    """Returns a price array for a time stamp within a duration or None if not found"""
    price_duration_list = []
    if t > int(df.last_valid_index().timestamp()+3600):
        return price_duration_list
    if t + duration <= int(df.first_valid_index().timestamp()):
        return price_duration_list
    if t < int(df.first_valid_index().timestamp()):
        price_duration_list.append((int(df.first_valid_index().timestamp()),df.iloc[0][uuid], duration+t-int(df.first_valid_index().timestamp())))
        return price_duration_list

    row_iterator = df.iterrows()
    for index, row in row_iterator:
        if t>=int(index.timestamp()) and t<int(index.timestamp()+3600):
            if t + duration <=int(index.timestamp()+3600):
                price_duration_list.append((t,row[uuid],duration))
                return price_duration_list
            else:
                if index == df.last_valid_index():
                    price_duration_list.append((t,row[uuid],int(index.timestamp())+3600-t))
                    return price_duration_list
                else:
                    next_index,next_row = next(row_iterator)
                    if index.timestamp()+3600 == next_index.timestamp():
                        price_duration_list.append((t,row[uuid],int(next_index.timestamp())-t))
                        price_duration_list.append((int(next_index.timestamp()),next_row[uuid],int(t +duration-next_index.timestamp())))
                        return price_duration_list
                    else:
                        if t> int(index.timestamp()) and t < int(index.timestamp()+3600):
                            price_duration_list.append((t,row[uuid],int(index.timestamp()+3600)-t))
                            return price_duration_list
        else:
            if t < int(index.timestamp()) and t+duration > int(index.timestamp()):
                price_duration_list.append((int(index.timestamp()),row[uuid],t + duration-int(index.timestamp())))
                return price_duration_list
    return price_duration_list


def get_window_in_string(seconds):
    if seconds%3600==0:
        return str(int(seconds/3600)) +'h'
    if seconds%60==0:
        return str(int(seconds/60)) +'m'
    return str(int(seconds))+'s'

def get_tariff_and_utility(request):
    """Returns tariff and utility for the specified building""" 
    df = pd.read_csv("price-mapping.csv")

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

def get_price(request, pymortar_client):
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
    if duration <= 0 or duration > 3600:
        return None, "invalid request, window is negative, zero, or greater than one hour max window is 1 hour"
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
    price_stream = pymortar.DataFrame(
        name="price_data",
        uuids=[uuid],
        aggregation=pymortar.MEAN,
        window="1h"
    )

    price_time_params = pymortar.TimeParams(
        start=rfc3339(int(request.start/1e9- request.start/1e9%3600)),
        end=rfc3339(int(end/1e9)),
    )

    price_request = pymortar.FetchRequest(
        sites=[""],
        dataFrames=[
            price_stream
        ],
        time=price_time_params
    )

    df = pymortar_client.fetch(price_request)["price_data"]

    print(df)
    print(df.empty)

    if df is None:
        return price_pb2.PriceReply(prices=[]), "did not fetch data from pymortar"
    if df.empty:
        return price_pb2.PriceReply(prices=[]), "empty data frame"
    df = df.dropna()
    print(df.empty)
    if df.empty:
        return price_pb2.PriceReply(prices=[]), "empty data frame"

    prices = []
    # if request starts on the hour
    if request.start/1e9%3600==0:
        # if window is one hour, return RAW data
        if duration == 3600:
            for index,row in df.iterrows():
                prices.append(price_pb2.PricePoint(time=int(index.timestamp()*1e9),price=row[uuid],unit=unit,window=request.window))
        # if window adds up to one hour, partition RAW data evenly
        elif 3600%duration==0:
            for index, row in df.iterrows():
                for i in range(int(index.timestamp()),int(index.timestamp())+3600,duration):
                    if i + duration <= request.end/1e9:
                        prices.append(price_pb2.PricePoint(time=int(i*1e9),price=row[uuid],unit=unit,window=request.window))

    # if request does not start on the hour
    else:
        # if window is one hour, return first partial hour, then RAW data
        if duration == 3600:
            i = request.start/1e9
            for index, row in df.iterrows():
                if i > index.timestamp():
                    prices.append(price_pb2.PricePoint(time=int(i*1e9),price=row[uuid],unit=unit, window=get_window_in_string(index.timestamp()+3600-i)))
                    i = index.timestamp()+3600
                elif i == index.timestamp():
                    prices.append(price_pb2.PricePoint(time=int(i*1e9),price=row[uuid],unit=unit, window=request.window))
                    i = index.timestamp()+3600
                else:
                    prices.append(price_pb2.PricePoint(time=int(index.timestamp()*1e9),price=row[uuid],unit=unit, window=request.window))
                    i = index.timestamp()+3600
        # if window adds up to one hour, return first partial window, then partition RAW data evenly
        elif 3600%duration==0:
            i = request.start/1e9
            for index, row in df.iterrows():
                if i > index.timestamp():
                    part_duration = i-index.timestamp()
                    if part_duration%duration !=0:
                        new_duration = (part_duration//duration +1)*duration
                        if i + new_duration-part_duration <= request.end/1e9:
                            prices.append(price_pb2.PricePoint(time=int(i*1e9),price=row[uuid],unit=unit,window=get_window_in_string(new_duration-part_duration)))
                        i = index.timestamp() + new_duration
                    while i < index.timestamp() + 3600:
                        if i + duration <= request.end/1e9:
                            prices.append(price_pb2.PricePoint(time=int(i*1e9),price=row[uuid],unit=unit, window=request.window))
                        i = i + duration
                elif i == index.timestamp():
                    for i in range(int(index.timestamp()),int(index.timestamp())+3600,duration):
                        if i + duration <= request.end/1e9:
                            prices.append(price_pb2.PricePoint(time=int(i*1e9),price=row[uuid],unit=unit,window=request.window))
                    i = index.timestamp()+3600
                else:
                    i = index.timestamp()
                    for i in range(int(index.timestamp()),int(index.timestamp())+3600,duration):
                        if i + duration <= request.end/1e9:
                            prices.append(price_pb2.PricePoint(time=int(i*1e9),price=row[uuid],unit=unit,window=request.window))
                    i = index.timestamp()+3600
    #if window does not add up to one to one hour, return corresponding data but split windows that overlap two hours
    if 3600%duration !=0:
        for i in range (int(request.start/1e9),int(request.end/1e9),duration):
            pd_list = get_price_for_interval(df,i,uuid,duration)
            for t,p,d in pd_list:
                if t + d <= request.end/1e9 and t + duration <=request.end/1e9:
                    prices.append(price_pb2.PricePoint(time=int(t*1e9),price=p,unit=unit,window=get_window_in_string(d)))

    return price_pb2.PriceReply(prices=prices), None

        # i = request.start/1e9
        # for index, row in df.iterrows():
        #     if i < index.timestamp():
        #         while i < int(index.timestamp()):
        #             i = i + duration
        #     if i + duration > int(df_index.timestamp()+3600):

        # row_iterator = df.iterrows()
        # df_index,df_row = row_iterator.next()
        # # Solve case when only one df
        # if len(df.index)==1:
        #     st = request.start/1e9
        #     while st < int(df_index.timestamp()):
        #         st = st + duration
        #     if st + duration > int(df_index.timestamp()+3600):
        #         if st < request.end/1e9:
        #             prices.append(price_pb2.PricePoint(time=int(st*1e9),price=df_row[uuid],unit=unit,window=get_window_in_string(int(df_index.timestamp())+3600-st)))
        #     else:
        #         for i in range(int(st),int(df_index.timestamp()+3600),duration):
        #             if i + duration > int(df_index.timestamp()+3600):
        #                 if i < request.end/1e9:
        #                     prices.append(price_pb2.PricePoint(time=int(i*1e9),price=df_row[uuid],unit=unit,window=get_window_in_string(int(df_index.timestamp())+3600-i)))
        #             else:
        #                 if i < request.end/1e9:
        #                     prices.append(price_pb2.PricePoint(time=int(i*1e9),price=df_row[uuid],unit=unit,window=request.window))
        #
        # # df has more than one item
        # else:
        #     df_next_index,df_next_row = row_iterator.next()
        #     for i in range(int(request.start/1e9),int(request.end/1e9),duration):
        #         while i < int(df_index.timestamp()):
        #             i = i + duration
        #         if i > df_index.timestamp():
        #
        #         if i+duration <= int(df_index.timestamp()+3600):
        #             if i < request.end/1e9:
        #                 prices.append(price_pb2.PricePoint(time=int(i*1e9),price=df_row[uuid],unit=unit,window=request.window))
        #         else:
        #             if df_next_index==df.last_valid_index():
        #                 if df_next_index==df_index+3600:
        #                     if i<int(df_next_index.timestamp()):
        #                         if i < request.end/1e9:
        #                             prices.append(price_pb2.PricePoint(time=int(i*1e9),price=df_row[uuid],unit=unit,window=get_window_in_string(int(df_next_index.timestamp())-i)))
        #                             prices.append(price_pb2.PricePoint(time=int(int(df_next_index.timestamp())*1e9),price=df_next_row[uuid],unit=unit,window=get_window_in_string(i+duration-int(df_next_index.timestamp()))))
        #                     else:
        #                         while (i < df_next_index.timestamp()+3600):
        #                             if i < request.end/1e9:
        #                                 if i + duration <= int(df_next_index.timestamp()+3600):
        #                                     prices.append(price_pb2.PricePoint(time=int(i*1e9),price=df_next_row[uuid],unit=unit,window=request.window))
        #                                 elif i + duration > int(df_next_index.timestamp()+3600):
        #                                     prices.append(price_pb2.PricePoint(time=int(i*1e9),price=df_next_row[uuid],unit=unit,window=get_window_in_string(int(df_next_index.timestamp())+3600-i)))
        #                             i = i + duration
        #                 else:
        #                     while i < int(df_next_index.timestamp()):
        #
        #
        #             else:
        #                 prices.append(price_pb2.PricePoint(time=int(i*1e9),price=df_row[uuid],unit=unit,window=get_window_in_string(int(df_next_index.timestamp())-i)))
        #                 prices.append(price_pb2.PricePoint(time=int(int(df_next_index.timestamp())*1e9),price=df_next_row[uuid],unit=unit,window=get_window_in_string(i+duration-int(df_next_index.timestamp()))))
        #                 df_index,df_row = df_next_index,df_next_row
        #                 df_next_index,df_next_row = row_iterator.next()
        #
    # return price_pb2.PriceReply(prices=prices), None


class PriceServicer(price_pb2_grpc.PriceServicer):
    def __init__(self):
        self.pymortar_client = pymortar.Client()

    def GetPrice(self, request, context):
        prices,error = get_price(request,self.pymortar_client)
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
        tariff_utility_reply,error = get_tariff_and_utility(request)
        if tariff_utility_reply is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(error)
            return price_pb2.TariffUtilityReply()
        elif error is not None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(error)
            return tariff_utility_reply

        return tariff_utility_reply


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    price_pb2_grpc.add_PriceServicer_to_server(PriceServicer(), server)
    server.add_insecure_port('localhost:50060')
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
