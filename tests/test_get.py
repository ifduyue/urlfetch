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
        i = random.randint(5, 50)
        query_string = {}
        for i in xrange(i):
            query_string[testlib.randstr()] = testlib.randstr()
        
        r = urlfetch.get('http://127.0.0.1:8800/?'+ urlfetch.urlencode(query_string))
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], urlfetch.urlencode(query_string))
        self.assertEqual(o['get'], query_string)


if __name__ == '__main__':
    unittest.main()
