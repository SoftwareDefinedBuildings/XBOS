from __future__ import absolute_import, division, print_function, unicode_literals
from xbos import get_client
from xbos.services.pundat import DataClient, make_dataframe
from xbos.services.hod import HodClient
import datetime
import pytz
import numpy as np
import pandas as pd
from datetime import timedelta
import datetime
from scipy import spatial
import math
from iec import IEC

##################################
# static variables
cons_col = 'House Consumption'
algorithm = 'Baseline Finder'
#

c = get_client()
archiver = DataClient(c)
#hod = HodClient("ciee/hod",c)

# Brick query needed here
uuid = '4d6e251a-48e1-3bc0-907d-7d5440c34bb9'
uuids = [uuid]
start = '"2017-08-21 00:00:00 PST"'
end = '"2017-08-31 00:00:00 PST"'

# Every 1 minute historical data
dfs = make_dataframe(archiver.window_uuids(uuids, end, start, '1min', timeout=120))

# GETTING DF from DICTIONARY (!):
df = dfs[uuid]
df=df.rename(columns = {'mean':cons_col})
df.index = df.index.tz_localize(pytz.utc) #UTC ?

# PREDICTION
pred = IEC(df).predict([algorithm])
print(pred)
