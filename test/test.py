import unittest

import os
import tempfile
import requests
import http.server
import threading
from datetime import datetime
import pytz
import time

from nordpool import elspot
from nordpool_db import NordpoolDb

import http.server # Our http server handler for http requests
from urllib.parse import quote

PORT = 9000

class StoppableHTTPServerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def parse_path_from_uri(self, uri):
        return quote(self.path, safe='/?&=')

    def do_GET(self):
        file_path = "test/httpd%s" % self.parse_path_from_uri(self.path)
        document_content = None
        if os.path.isfile(file_path):
            f = open(file_path)
            document_content = f.read()
            f.close()

        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(bytes('Hello world!\n', 'utf-8'))
        elif document_content is not None:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(document_content, 'utf-8'))
        else:
            self.send_error(404)

class StoppableHTTPServer(http.server.HTTPServer):
    def run(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            # Clean-up server (close socket, etc.)
            self.server_close()

class TestGeneral(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.server = StoppableHTTPServer(("127.0.0.1", 4141), StoppableHTTPServerRequestHandler)
        self.thread = threading.Thread(None, self.server.run)
        self.thread.start()

        self.TZ_DEFAULT = pytz.timezone('UTC')

    @classmethod
    def tearDownClass(self):
        self.server.shutdown()
        self.thread.join()

    def test_create_and_simple_unit_tests(self):
        tmp_handle, tmp_name = tempfile.mkstemp(prefix='npdb_test_')
        os.close(tmp_handle)

        npdb = NordpoolDb(tmp_name)

        # datetime_to_sqlstring()
        test_cases = [
            [datetime(1971, 9, 11), '1971-09-11 00:00:00'],
            [datetime(2034, 12, 1, 3, 4, 5), '2034-12-01 03:04:05'],
        ]

        for this_case in test_cases:
            self.assertEqual(npdb.datetime_to_sqlstring(this_case[0]), this_case[1])

        del npdb

        self.assertTrue(os.path.exists(tmp_name))

        os.remove(tmp_name)

    def test_httpd_alive(self):
        response = requests.get("http://localhost:4141/")
        response_content = response.content

        self.assertEqual(response_content.decode('utf-8'), 'Hello world!\n', msg="httpd server does not respond")

    def test_correct_currency(self):
        prices_spot = elspot.Prices()
        prices_spot.API_URL = 'http://localhost:4141/%i'

        result = prices_spot.hourly(areas=['FI'], end_date=datetime(2022,11,3))
        self.assertEqual(result['currency'], 'EUR')
    
    def test_store_and_retrieve_prices(self):
        prices_spot = elspot.Prices()
        prices_spot.API_URL = 'http://localhost:4141/%i'

        tmp_handle, tmp_name = tempfile.mkstemp(prefix='npdb_test_')
        os.close(tmp_handle)

        npdb = NordpoolDb(tmp_name)

        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime(2022,11,3)))
        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime(2022,11,2)))
        # Do this again to make sure you can add same dataset over and over again
        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime(2022,11,2)))

        TZ_EET = pytz.timezone('EET')

        test_cases = [
            # Timezone support
            [self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 1, 20, 0)), 100.9],
            [TZ_EET.localize(datetime(2022, 11, 2, 1, 20, 0)), 106.38],

            # Even hour
            [self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 1, 0, 0)), 100.9],
 
            # Different date than the previous one
            [self.TZ_DEFAULT.localize(datetime(2022, 11, 3, 1, 20, 0)), 29.24],

            # Not in the dataset
            [self.TZ_DEFAULT.localize(datetime(2022, 11, 1, 12, 0, 0)), None],
        ]

        for this_case in test_cases:
            self.assertEqual(npdb.get_price_value('FI', this_case[0]), this_case[1])
        
        npdb.db_add_or_update_price_value(
            'FI',
            datetime(2022, 11, 2, 1, 0, 0),
            datetime(2022, 11, 2, 2, 0, 0),
            200.5
        )

        self.assertEqual(npdb.get_price_value('FI', self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 1, 30, 0))), 200.5)

        del npdb

        os.remove(tmp_name)
    
    def test_price_rank(self):
        prices_spot = elspot.Prices()
        prices_spot.API_URL = 'http://localhost:4141/%i'

        tmp_handle, tmp_name = tempfile.mkstemp(prefix='npdb_test_')
        os.close(tmp_handle)

        npdb = NordpoolDb(tmp_name)

        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime(2022,11,3)))
        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime(2022,11,2)))

        TZ_EET = pytz.timezone('EET')

        test_cases = [
            # Check timezone support
            [
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 16, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 19, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 17, 30)),
                (2, 3)
            ],
            [
                TZ_EET.localize(datetime(2022, 11, 2, 16, 0)),
                TZ_EET.localize(datetime(2022, 11, 2, 19, 0)),
                TZ_EET.localize(datetime(2022, 11, 2, 17, 30)),
                (3, 3)
            ],


            [
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 5, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 8, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 7, 0)),
                (1, 3)
            ],

            # Observation period stretches over midnight
            [
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 0, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 3, 0, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 3, 20)),
                (6, 24)
            ],

            # Target time is not in the observation period
            [
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 5, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 3, 6, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 1, 0, 0)),
                (None, 25)
            ],

            [
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 5, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 3, 6, 0)),
                self.TZ_DEFAULT.localize(datetime(2022, 11, 2, 6, 30)),
                (24, 25)
            ],
        ]

        for this_case in test_cases:
            self.assertEqual(npdb.get_price_rank('FI', this_case[0], this_case[1], this_case[2]), this_case[3])

        del npdb

        os.remove(tmp_name)
    
    def test_get_seconds_from_last_update(self):
        prices_spot = elspot.Prices()
        prices_spot.API_URL = 'http://localhost:4141/%i'

        tmp_handle, tmp_name = tempfile.mkstemp(prefix='npdb_test_')
        os.close(tmp_handle)

        npdb = NordpoolDb(tmp_name)

        self.assertIsNone(npdb.get_seconds_from_last_update('FI'))

        npdb.update_data(prices_spot.hourly(areas=['FI'], end_date=datetime(2022,11,3)))

        self.assertIsNotNone(npdb.get_seconds_from_last_update('FI'))
        self.assertTrue(npdb.get_seconds_from_last_update('FI') < 2)

        time.sleep(5)

        self.assertTrue(npdb.get_seconds_from_last_update('FI') >= 5)

        del npdb

        os.remove(tmp_name)



if __name__ == '__main__':
    unittest.main()
