from datetime import datetime, date, timedelta
import pytz
OURTZ=pytz.timezone("US/Pacific")
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
    return OURTZ.localize(dt)

def get_today():
    d = datetime.now(OURTZ)
    return OURTZ.localize(datetime(year=d.year, month=d.month, day=d.day))

def get_tomorrow():
    d = datetime.now(OURTZ) + timedelta(days=1)
    return OURTZ.localize(datetime(year=d.year, month=d.month, day=d.day))
