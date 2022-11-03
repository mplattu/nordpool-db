import sqlite3

from nordpool import elspot, elbas
from pprint import pprint

class NordpoolDb:
    sqlite_path = None
    sqlite_con = None

    def __init__(self, sqlite_path):
        self.sqlite_path = sqlite_path
        self.sqlite_con = sqlite3.connect(sqlite_path)
    
    def __del__(self):
        self.sqlite_con.close()
    
    def datetime_to_sqlstring(self, datetime_param):
        return datetime_param.strftime('%Y-%m-%d %H-%M-%S')

    def update_data(self, new_nordpool_data):
        '''
        Update database with given new_nordpool_data. This is a output of
        Nordpool::Price() function:

        prices_spot = elspot.Prices()
        my_nordpool_db.update_data(prices_spot.prices_spot.hourly(areas=['FI']))
        '''

        pprint(new_nordpool_data)

        for this_area in new_nordpool_data['areas'].keys():
            print(f"This area: {this_area}\n")
            for this_value in new_nordpool_data[this_area]['values']:
                sql_datetime_start = self.datetime_to_sqlstring(this_value['start'])
                sql_datetime_end = self.datetime_to_sqlstring(this_value['end'])
                value = this_value['value']

        print(f"This currency: {new_nordpool_data['currency']}\n")
    
