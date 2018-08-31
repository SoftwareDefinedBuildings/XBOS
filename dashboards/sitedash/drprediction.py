from datetime import datetime, date, timedelta
import msgpack
from dateutil import rrule
from util import get_today
from xbos import get_client
import random

#def get_prediction():
#    # dummy
#    pred_start = get_today()
#    pred_end = pred_start + timedelta(days=3)
#    pred_days = list(rrule.rrule(freq=rrule.DAILY, dtstart=pred_start, until=pred_end))
#
#    days = []
#    for pred_day in pred_days:
#        days.append({pred_day.strftime('%s'): random.choice(['unlikely','possible','likely'])})
#
#    return {
#        'days': days
#    }


def get_prediction(provider):
    c = get_client()
    days = []

    msg = c.query('{0}/forecast/demand_response/s.forecast_demand_response/dr/i.xbos.demand_response_forecast/signal/info'.format(provider))
    if len(msg) == 0: return
    pos = msg[0].payload_objects
    if len(pos) == 0: return
    forecasts = msgpack.unpackb(pos[0].content)
    for forecast in forecasts:
        day = datetime.fromtimestamp(forecast.get('Date') / 1e9)
        print(forecast)
        likelihood = ['unlikely','possible','likely','confirmed'][forecast.get('Event_likelihood')]
        print('DR event?',day,'=>',likelihood)
        days.append({'date': int(forecast.get('Date')/1e9), 'likelihood': likelihood})

    msg = c.query('{0}/confirmed/demand_response/s.confirmed_demand_response/dr/i.xbos.demand_response_confirmed/signal/info'.format(provider))
    if len(msg) == 0: return
    pos = msg[0].payload_objects
    if len(pos) == 0: return
    forecast = msgpack.unpackb(pos[0].content)
    day = datetime.fromtimestamp(forecast.get('Date') / 1e9)
    likelihood = ['no event','confirmed'][forecast.get('Event_status')]
    print('DR event?',day,'=>',likelihood)
    days.append({'date': int(forecast.get('Date')/1e9), 'likelihood': likelihood})

    return days


