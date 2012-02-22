import unittest
import urlfetch
import json
import random

import testlib

class GetTest(unittest.TestCase):

    def test_fetch(self):
        r = urlfetch.fetch('http://127.0.0.1:8800/')
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')

    def test_get(self):
        r = urlfetch.get('http://127.0.0.1:8800/')
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')

    def test_query_string(self):
        qs = testlib.randdict()
        query_string = urlfetch.urlencode(qs)
        
        r = urlfetch.get('http://127.0.0.1:8800/?'+ query_string)
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)


if __name__ == '__main__':
    unittest.main()
