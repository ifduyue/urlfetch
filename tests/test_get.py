import testlib
import urlfetch

import unittest
import json
import random
import socket


class GetTest(unittest.TestCase):

    def test_fetch(self):
        r = urlfetch.fetch(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')

    def test_get(self):
        r = urlfetch.get(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        
    def test_fragment(self):
        r = urlfetch.get(testlib.test_server_host + '#urlfetch')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')

    def test_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        r = urlfetch.get(testlib.test_server_host + '?'+ query_string)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)
        
    def test_fragment_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        r = urlfetch.get(testlib.test_server_host + '?'+ query_string + '#urlfetch')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_basic_auth(self):
        h = urlfetch.Headers()
        h.basic_auth('urlfetch', 'fetchurl')
        r = urlfetch.get(testlib.test_server_host + 'basic_auth', headers=h.items())
        o = json.loads(r.text)
        
        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        
    def test_fragment_basic_auth(self):
        h = urlfetch.Headers()
        h.basic_auth('urlfetch', 'fetchurl')
        r = urlfetch.get(testlib.test_server_host + 'basic_auth#urlfetch', headers=h.items())
        o = json.loads(r.text)
        
        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')

    def test_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        h = urlfetch.Headers()
        h.basic_auth('urlfetch', 'fetchurl')
        r = urlfetch.get(testlib.test_server_host + 'basic_auth?'+ query_string, headers=h.items())
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)
        
    def test_fragment_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        h = urlfetch.Headers()
        h.basic_auth('urlfetch', 'fetchurl')
        r = urlfetch.get(testlib.test_server_host + 'basic_auth?'+ query_string + '#urlfetch', headers=h.items())
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_timeout(self):
        self.assertRaises(socket.timeout, lambda:urlfetch.get(testlib.test_server_host + 'sleep/1', timeout=0.5))


if __name__ == '__main__':
    unittest.main()
