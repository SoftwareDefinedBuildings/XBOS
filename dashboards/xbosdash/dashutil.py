import pytz
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta

TZ = pytz.timezone('US/Pacific')

def get_today():
    d = datetime.now(TZ)
    return TZ.localize(datetime(year=d.year, month=d.month, day=d.day))

def prevmonday(num):
    """
    Return unix SECOND timestamp of "num" mondays ago
    """
    today = get_today()
    lastmonday = today - timedelta(days=today.weekday(), weeks=num)
    return lastmonday

def get_start(last):
    today = get_today()
    if last == 'year':
        dt = datetime(year=today.year, month=1, day=1)
    elif last == 'month':
        dt = datetime(year=today.year, month=today.month, day=1)
    elif last == 'week':
        dt = datetime(year=today.year, month=today.month, day=today.day-today.weekday())
    elif last == 'day':
        dt = datetime(year=today.year, month=today.month, day=today.day)
    elif last == 'hour':
        dt = datetime(year=today.year, month=today.month, day=today.day, hour=datetime.now().hour)
    else:
        dt = datetime(year=today.year, month=today.month, day=today.day, hour=datetime.now().hour)
    return TZ.localize(dt)

def generate_months(lastN):
    firstDayThisMonth = get_today().replace(day=1)
    ranges = [[get_today(), firstDayThisMonth]]
    lastN = int(lastN)
    while lastN > 0:
        firstDayLastMonth = firstDayThisMonth - relativedelta(months=1)
        ranges.append([firstDayThisMonth - timedelta(days=1) + timedelta(hours=1), firstDayLastMonth])
        firstDayThisMonth = firstDayLastMonth
        lastN -= 1
    return ranges


