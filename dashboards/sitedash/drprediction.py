from datetime import datetime, date, timedelta
from dateutil import rrule
from util import get_today
import random

def get_prediction():
    # dummy
    pred_start = get_today()
    pred_end = pred_start + timedelta(days=3)
    pred_days = list(rrule.rrule(freq=rrule.DAILY, dtstart=pred_start, until=pred_end))

    days = []
    for pred_day in pred_days:
        days.append({pred_day.strftime('%s'): random.choice(['unlikely','possible','likely'])})

    return {
        'days': days
    }
