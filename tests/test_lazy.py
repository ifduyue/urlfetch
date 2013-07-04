import testlib
import urlfetch
import unittest
import time
import json
import socket

class LazyTest(unittest.TestCase):

    def test_lazy(self):

        time1 = time.time()
        r = urlfetch.get(testlib.test_server_host + 'sleep/2', lazy=True)
        time2 = time.time()

        self.assertLess(time2 - time1, 1)
        
        time.sleep(2)

        time3 = time.time()
        o = json.loads(r.text)
        time4 = time.time()

        self.assertLess(time4 - time3, 1)
        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')

    def test_timeout(self):
        r = urlfetch.get(testlib.test_server_host + 'sleep/1', lazy=True)
        r.timeout = 0.5
        self.assertRaises(socket.timeout, lambda: r.text)

        r = urlfetch.get(testlib.test_server_host + 'sleep/1', lazy=True)
        r.timeout = 0.5
        time.sleep(2)
        self.assertEqual(r.status, 200)


if __name__ == '__main__':
    unittest.main()
