import sqlite3
from datetime import datetime
import pytz

from nordpool import elspot, elbas

class NordpoolDb:
    sqlite_path = None
    sqlite_con = None

    def __init__(self, sqlite_path):
        self.sqlite_path = sqlite_path
        self.sqlite_con = sqlite3.connect(sqlite_path)
        self.PRICE_VALUE_IS_NOT_DEFINED = float('inf')
        self.NORDPOOL_TZ = pytz.timezone('UTC')

        self.create_database()

        #self.sqlite_con.set_trace_callback(print)

    def __del__(self):
        self.sqlite_con.close()
    
    def create_database(self):
        cursor = self.sqlite_con.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS `prices`
                (
                    [area] TEXT,
                    [start] DATETIME,
                    [end] DATETIME,
                    [value] FLOAT
                )
            ''')
        self.sqlite_con.commit()

    def datetime_to_sqlstring(self, datetime_param):
        return datetime_param.strftime('%Y-%m-%d %H:%M:%S')

    def db_add_or_update_price_value(self, area, datetime_start, datetime_end, price_value):
        if price_value == self.PRICE_VALUE_IS_NOT_DEFINED:
            return

        datetime_start_str = self.datetime_to_sqlstring(datetime_start)
        datetime_end_str = self.datetime_to_sqlstring(datetime_end)

        cursor = self.sqlite_con.cursor()

        sql_update = "UPDATE `prices` SET `value`=? WHERE `area`=? AND `start`=? AND `end`=?"
        cursor.execute(sql_update, (price_value, area, datetime_start_str, datetime_end_str))
        if cursor.rowcount == 0:
            sql_insert = "INSERT INTO `prices` (`area`, `start`, `end`, `value`) VALUES (?, ?, ?, ?);"
            cursor.execute(sql_insert, (area, datetime_start_str, datetime_end_str, price_value))

        self.sqlite_con.commit()

    def update_data(self, new_nordpool_data):
        '''
        Update database with given new_nordpool_data. This is a output of
        Nordpool::Price() function:

        prices_spot = elspot.Prices()
        my_nordpool_db.update_data(prices_spot.prices_spot.hourly(areas=['FI']))
        '''

        for this_area in new_nordpool_data['areas'].keys():
            for this_value in new_nordpool_data['areas'][this_area]['values']:
                self.db_add_or_update_price_value(this_area, this_value['start'], this_value['end'], this_value['value'])
    
    def get_price_value(self, area, datetime_param):
        datetime_utc = datetime_param.astimezone(self.NORDPOOL_TZ)
        datetime_utc_str = self.datetime_to_sqlstring(datetime_utc)

        cursor = self.sqlite_con.cursor()

        sql = "SELECT `value` FROM `prices` WHERE `area`=? AND `start`<=? AND `end`>?"

        cursor.execute(sql, (area, datetime_utc_str, datetime_utc_str))

        rows = cursor.fetchall()

        price_value = None

        if len(rows) > 1:
            raise Exception(f'More than one price value ({len(rows)})')
        
        for this_row in rows:
            price_value = rows[0][0]
        
        return price_value
    
    def get_price_rank(self, area, period_start, period_end, target_time):
        period_start_str = self.datetime_to_sqlstring(period_start.astimezone(self.NORDPOOL_TZ))
        period_end_str = self.datetime_to_sqlstring(period_end.astimezone(self.NORDPOOL_TZ))
        target_hours_str = datetime.strptime(target_time.astimezone(self.NORDPOOL_TZ).strftime('%Y-%m-%d %H:00:00'), '%Y-%m-%d %H:%M:%S')

        cursor = self.sqlite_con.cursor()

        sql = "SELECT (`start`=?) AS `is_target`, `start`, `end` FROM `prices` WHERE `area`=? AND `start`>=? AND `end`<=? ORDER BY `value` ASC"

        cursor.execute(sql, (target_hours_str, area, period_start_str, period_end_str))

        observed_rank = None
        observed_row_count = 0

        for row in cursor:
            observed_row_count += 1
            if row[0] == 1:
                observed_rank = observed_row_count

        return (observed_rank, observed_row_count)
