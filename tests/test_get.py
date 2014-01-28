import testlib
from testlib import randstr
import urlfetch

import unittest
import json
import os
import socket
import tempfile


class GetTest(unittest.TestCase):

    def test_fetch(self):
        r = urlfetch.fetch(testlib.url())
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
        r = urlfetch.get(testlib.url())
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')

    def test_get_params(self):
        p1 = (randstr(), randstr())
        p2 = (randstr(), randstr())
        params = dict((p1, p2))
        r = urlfetch.get(testlib.test_server_host, params=params)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        self.assertTrue(('%s=%s' % p1) in r.url)
        self.assertTrue(('%s=%s' % p2) in r.url)

    def test_fragment(self):
        r = urlfetch.get(testlib.url('#urlfetch'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')

    def test_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)

        r = urlfetch.get(testlib.url('?'+ query_string))
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

        r = urlfetch.get(testlib.url('?'+ query_string + '#urlfetch'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_basic_auth(self):
        r = urlfetch.get(testlib.url('basic_auth'), auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')

    def test_fragment_basic_auth(self):
        r = urlfetch.get(testlib.url('basic_auth#urlfetch'), auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')

    def test_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)

        r = urlfetch.get(testlib.url('basic_auth?'+ query_string), auth=('urlfetch', 'fetchurl'))
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

        r = urlfetch.get(testlib.url('basic_auth?'+ query_string + '#urlfetch'), auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_timeout(self):
        self.assertRaises(socket.timeout, lambda: urlfetch.get(testlib.url('sleep/1'), timeout=0.5))

    def test_length_limit(self):
        self.assertRaises(urlfetch.UrlfetchException, lambda: urlfetch.get(testlib.url(), length_limit=1))

    def test_streaming(self):
        with tempfile.TemporaryFile() as f:
            with urlfetch.get(testlib.url('utf8.txt')) as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            self.assertEqual(f.read(), open(os.path.join(os.path.dirname(__file__), 'test.file'), 'rb').read())

        with tempfile.TemporaryFile() as f:
            with urlfetch.get(testlib.url('/gbk.txt')) as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            self.assertEqual(f.read(), open(os.path.join(os.path.dirname(__file__), 'test.file.gbk'), 'rb').read())

    def test_cookie(self):
        cookie = (randstr(), randstr())
        r = urlfetch.get(testlib.url('setcookie/%s/%s' % cookie))
        self.assertEqual(r.cookies[cookie[0]], cookie[1])
        self.assertTrue(('%s=%s' % cookie) in r.cookiestring)

    def test_redirect(self):
        r = urlfetch.get(testlib.url('/redirect/3/0'))
        self.assertTrue(r.status in (301, 302, 303, 307))
        self.assertTrue('location' in r.headers)

        self.assertRaises(urlfetch.UrlfetchException, lambda: urlfetch.get(testlib.url('/redirect/3/0'), max_redirects=1))


if __name__ == '__main__':
    unittest.main()
