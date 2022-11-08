#!/usr/bin/env python3

import os
from datetime import datetime, timedelta
import pytz

from nordpool import elspot
from nordpool_db import nordpool_db

SQLITE_DB = "/tmp/npdb_example.db"

AREA = 'FI'
TZ = 'EET'

prices_spot = elspot.Prices()

if os.path.isfile(SQLITE_DB):
    print(f'Warning: Using your existing database at {SQLITE_DB}')

npdb = nordpool_db.NordpoolDb(SQLITE_DB)
tz = pytz.timezone(TZ)
dt_yesterday = tz.localize(datetime.today()-timedelta(days=1))

# Fetch yesterday
npdb.update_data(prices_spot.hourly(areas=[AREA], end_date=dt_yesterday))

dt_yesterday_start = datetime.strptime(dt_yesterday.strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
dt_yesterday_end = dt_yesterday_start + timedelta(days=1)

time_pointer = dt_yesterday_start

while (time_pointer < dt_yesterday_end):
    print(time_pointer.strftime('%Y-%m-%d %H:%M'), end='\t')

    price = npdb.get_price_value(AREA, time_pointer)
    rank = npdb.get_price_rank(AREA, dt_yesterday_start, dt_yesterday_end, time_pointer)

    print(f'{price}\t{rank[0]}')

    time_pointer += timedelta(hours=1)
