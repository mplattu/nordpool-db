import unittest

import os
import tempfile
import requests
import http.server
import threading

from nordpool import elspot
from nordpool_db import NordpoolDb

import http.server # Our http server handler for http requests
import socketserver # Establish the TCP Socket connections
from urllib.parse import urlparse
from urllib.parse import quote

PORT = 9000

class StoppableHTTPServerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def parse_path_from_uri(self, uri):
        parsed_uri = urlparse(self.path)
        return quote(parsed_uri.path, safe='/')

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

    @classmethod
    def tearDownClass(self):
        self.server.shutdown()
        self.thread.join()

    def test_create(self):
        tmp_handle, tmp_name = tempfile.mkstemp(prefix='npdb_test_')
        os.close(tmp_handle)

        npdb = NordpoolDb(tmp_name)
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

        result = prices_spot.hourly(areas=['FI'])
        self.assertEqual(result['currency'], 'EUR')


if __name__ == '__main__':
    unittest.main()
