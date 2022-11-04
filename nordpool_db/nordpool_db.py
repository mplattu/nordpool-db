import sqlite3

from nordpool import elspot, elbas
from pprint import pprint

class NordpoolDb:
    sqlite_path = None
    sqlite_con = None

    def __init__(self, sqlite_path):
        self.sqlite_path = sqlite_path
        self.sqlite_con = sqlite3.connect(sqlite_path)

        self.create_database()

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

    def db_add_price_value(self, area, datetime_start, datetime_end, price_value):
        datetime_start_str = self.datetime_to_sqlstring(datetime_start)
        datetime_end_str = self.datetime_to_sqlstring(datetime_end)

        cursor = self.sqlite_con.cursor()

        sql = "INSERT INTO `prices` (`area`, `start`, `end`, `value`) VALUES (?, ?, ?, ?);"

        cursor.execute(sql, (area, datetime_start_str, datetime_end_str, price_value))
        self.sqlite_con.commit()

    def update_data(self, new_nordpool_data):
        '''
        Update database with given new_nordpool_data. This is a output of
        Nordpool::Price() function:

        prices_spot = elspot.Prices()
        my_nordpool_db.update_data(prices_spot.prices_spot.hourly(areas=['FI']))
        '''

        for this_area in new_nordpool_data['areas'].keys():
            print(f"This area: {this_area}\n")
            for this_value in new_nordpool_data['areas'][this_area]['values']:
                self.db_add_price_value(this_area, this_value['start'], this_value['end'], this_value['value'])
    
    def get_price_value(self, area, datetime_param):
        datetime_str = self.datetime_to_sqlstring(datetime_param)

        cursor = self.sqlite_con.cursor()

        sql = "SELECT `value` FROM `prices` WHERE `area`=? AND `start`<=? AND `end`>?"

        cursor.execute(sql, (area, datetime_str, datetime_str))

        rows = cursor.fetchall()

        price_value = None

        if len(rows) > 1:
            raise Exception(f'More than one price value ({len(rows)})')
        
        for this_row in rows:
            price_value = rows[0][0]
        
        return price_value
    
