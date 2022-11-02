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
        
    def update_data(self, new_nordpool_data):
        '''
        Update database with given new_nordpool_data. This is a output of
        Nordpool::Price() function:

        prices_spot = elspot.Prices()
        my_nordpool_db.update_data(prices_spot.prices_spot.hourly(areas=['FI']))
        '''

        pprint(new_nordpool_data)
    
