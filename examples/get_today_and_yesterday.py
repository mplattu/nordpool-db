#!/usr/bin/env python3

from datetime import date, timedelta

from nordpool import elspot
from nordpool_db import NordpoolDb

SQLITE_DB = "/tmp/nbdp_example.db"
AREAS = ['FI']

prices_spot = elspot.Prices()

nordpool_db = NordpoolDb(SQLITE_DB)

# Fetch today
nordpool_db.update_data(prices_spot.hourly(areas=AREAS, end_date=date.today()))

# Fetch yesterday
nordpool_db.update_data(prices_spot.hourly(areas=AREAS, end_date=date.today()-timedelta(days=1)))
