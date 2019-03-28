import pymortar
from rfc3339 import rfc3339

price_stream = pymortar.DataFrame(
    name="price_data",
    uuids=["c0537318-3dd6-3b06-832f-23c413eb54d3"]
    aggregation=pymortar.MEAN,
    window="1h"
)

price_time_params = pymortar.TimeParams(
    start=rfc3339(time.gmtime(int(request.start/1e9- request.start/1e9%3600))),
    end=rfc3339(time.gmtime(int(end/1e9))),
)

request = pymortar.FetchRequest(
    dataFrames=[
        price_stream
    ],
    time=price_time_params
)

price_data = pymortar_client.fetch(request)['price_data']

print(price_data)



