import pymortar
import time
import pytz
import datetime
from rfc3339 import rfc3339
import numpy as np
import pandas as pd

pymortar_client = pymortar.Client()

"""For the first interval below, the query returns all NaN values for an unknown reason while the 
second time interval returns all 0s for the price. Comment each one out separately to see the two cases"""

uuid = '6ec2b69f-ed98-3b58-b664-fedc3e0ebc3a'
print(pymortar_client)

#Case 1: This query returns all NaN values for this time interval
# end = datetime.datetime.now().replace(tzinfo=pytz.utc) - datetime.timedelta(weeks=52)
# start = end - datetime.timedelta(days=10)
# start = int(time.mktime(start.timetuple())*1e9)
# end =  int(time.mktime(end.timetuple())*1e9)

# Case 2: This query returns values, but all the prices are 0 for this time interval
# start = int(time.mktime(datetime.datetime.strptime("2/02/2019 2:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
# end =  int(time.mktime(datetime.datetime.strptime("2/02/2019 22:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)

start = int(time.mktime(datetime.datetime.strptime("20/04/2019 01:00:00", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)
end =  int(time.mktime(datetime.datetime.strptime("27/04/2019 23:59:59", "%d/%m/%Y %H:%M:%S").timetuple())*1e9)

print(start)
print(end)
print(uuid)

price_stream = pymortar.DataFrame(
    name="price_data",
    uuids=[uuid],
    aggregation=pymortar.MEAN,
    window="1h"
)

price_time_params = pymortar.TimeParams(
    start=rfc3339(int(start/1e9- start/1e9%3600)),
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

df.to_csv("new.csv")

print(df)
