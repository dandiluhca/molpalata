import unittest
import json
from http.client import HTTPConnection
import threading
import os
import importlib

app = None

class ServerThread(threading.Thread):
    def run(self):
        self.httpd = app.HTTPServer(('localhost', 3001), app.Handler)
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()

class BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global app
        if os.path.exists('db.sqlite'):
            os.remove('db.sqlite')
        app = importlib.import_module('app')
        cls.server = ServerThread()
        cls.server.daemon = True
        cls.server.start()
        import time
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def test_register_and_login(self):
        conn = HTTPConnection('localhost', 3001)
        user = {
            'full_name': 'Test User',
            'birth_date': '2000-01-01',
            'phone': '123',
            'username': 'test',
            'email': 'test@example.com',
            'password': 'pass'
        }
        body = json.dumps(user)
        conn.request('POST', '/api/auth/register', body, {'Content-Type': 'application/json'})
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        conn.request('POST', '/api/auth/login', json.dumps({'email': user['email'], 'password': user['password']}), {'Content-Type': 'application/json'})
        res = conn.getresponse()
        self.assertEqual(res.status, 200)
        data = json.loads(res.read())
        self.assertIn('token', data)
        conn.close()

if __name__ == '__main__':
    unittest.main()
