import testlib
import urlfetch

import unittest
import json
import os
import socket
import tempfile


class GetTest(unittest.TestCase):

    def test_fetch(self):
        r = urlfetch.fetch(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')

    def test_fetch_data(self,):
        r = urlfetch.fetch(testlib.test_server_host, data='foo=bar')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
    

    def test_get(self):
        r = urlfetch.get(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        
    def test_fragment(self):
        r = urlfetch.get(testlib.test_server_host + '#urlfetch')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')

    def test_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        r = urlfetch.get(testlib.test_server_host + '?'+ query_string)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)
        
    def test_fragment_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        r = urlfetch.get(testlib.test_server_host + '?'+ query_string + '#urlfetch')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_basic_auth(self):
        r = urlfetch.get(testlib.test_server_host + 'basic_auth', auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)
        
        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        
    def test_fragment_basic_auth(self):
        r = urlfetch.get(testlib.test_server_host + 'basic_auth#urlfetch', auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)
        
        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')

    def test_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        r = urlfetch.get(testlib.test_server_host + 'basic_auth?'+ query_string, auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)
        
    def test_fragment_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        r = urlfetch.get(testlib.test_server_host + 'basic_auth?'+ query_string + '#urlfetch', auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_timeout(self):
        self.assertRaises(socket.timeout, lambda: urlfetch.get(testlib.test_server_host + 'sleep/1', timeout=0.5))

    def test_length_limit(self):
        self.assertRaises(urlfetch.UrlfetchException, lambda: urlfetch.get(testlib.test_server_host, length_limit=1))

    def test_streaming(self):
        with tempfile.TemporaryFile() as f:
            with urlfetch.get(testlib.test_server_host + '/utf8.txt') as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            self.assertEqual(f.read(), open(os.path.join(os.path.dirname(__file__), 'test.file'), 'rb').read())

        with tempfile.TemporaryFile() as f:
            with urlfetch.get(testlib.test_server_host + '/gbk.txt') as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            self.assertEqual(f.read(), open(os.path.join(os.path.dirname(__file__), 'test.file.gbk'), 'rb').read())

    def test_cookie(self):
        randstr = testlib.randstr
        cookie = (randstr(), randstr())
        r = urlfetch.get(testlib.test_server_host + 'setcookie/%s/%s' % cookie)
        self.assertEqual(r.cookies[cookie[0]], cookie[1])
        self.assertTrue(('%s=%s' % cookie) in r.cookiestring)


if __name__ == '__main__':
    unittest.main()
