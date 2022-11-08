#!/usr/bin/env python3

import os
from datetime import datetime, timedelta

from nordpool import elspot
from nordpool_db import nordpool_db

SQLITE_DB = "/tmp/npdb_example.db"
AREAS = ['FI', 'EE']

prices_spot = elspot.Prices()

if os.path.isfile(SQLITE_DB):
    print(f'Warning: Using your existing database at {SQLITE_DB}')

nordpool_db = nordpool_db.NordpoolDb(SQLITE_DB)

dt_today = datetime.today()
dt_yesterday = datetime.today()-timedelta(days=1)
dt_tomorrow = datetime.today()+timedelta(days=1)

# Fetch today
nordpool_db.update_data(prices_spot.hourly(areas=AREAS, end_date=dt_today))

# Fetch yesterday
nordpool_db.update_data(prices_spot.hourly(areas=AREAS, end_date=dt_yesterday))

# Fetch tomorrow
nordpool_db.update_data(prices_spot.hourly(areas=AREAS, end_date=dt_tomorrow))

# Create start/pointer time and end time for a loop
time_current = datetime.strptime(dt_yesterday.strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d %H:%M:%S')
time_end = datetime.strptime(dt_tomorrow.strftime('%Y-%m-%d 23:59:59'), '%Y-%m-%d %H:%M:%S')

while (time_current <= time_end):
    print(time_current.strftime('%Y-%m-%d %H:%M'), end='\t')

    for this_area in AREAS:
        price = nordpool_db.get_price_value(this_area, time_current)
        print(f'{this_area}:{price}', end='\t')

    time_current += timedelta(hours=1)

    print('')
