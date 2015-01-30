import testlib
from testlib import randstr
import urlfetch

import unittest
import json
import os
import tempfile


class GetTest(unittest.TestCase):

    def test_fetch(self):
        r = urlfetch.fetch(testlib.url())
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'GET')

    def test_json(self):
        url = testlib.url('utf8.txt')
        call = lambda: urlfetch.get(url).json
        self.assertRaises(urlfetch.ContentDecodingError, call)

    def test_fetch_data(self,):
        r = urlfetch.fetch(testlib.test_server_host, data='foo=bar')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'POST')

    def test_get(self):
        r = urlfetch.get(testlib.url())
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
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
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'GET')
        self.assertTrue(('%s=%s' % p1) in r.url)
        self.assertTrue(('%s=%s' % p2) in r.url)

    def test_fragment(self):
        r = urlfetch.get(testlib.url('#urlfetch'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'GET')

    def test_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)

        r = urlfetch.get(testlib.url('?'+ query_string))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
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
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_basic_auth(self):
        r = urlfetch.get(testlib.url('basic_auth'), auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'GET')

    def test_fragment_basic_auth(self):
        r = urlfetch.get(testlib.url('basic_auth#urlfetch'), auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'GET')

    def test_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)

        r = urlfetch.get(testlib.url('basic_auth?'+ query_string), auth=('urlfetch', 'fetchurl'))
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(r.links, [])
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
        self.assertEqual(r.links, [])
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_timeout(self):
        self.assertRaises(urlfetch.Timeout, lambda: urlfetch.get(testlib.url('sleep/1'), timeout=0.5))

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

    def test_compressed_streaming(self):
        sina = urlfetch.b('sina')

        with tempfile.TemporaryFile() as f:
            with urlfetch.get('http://news.sina.com.cn/') as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            html = f.read()
            self.assertTrue(sina in html)

        with tempfile.TemporaryFile() as f:
            with urlfetch.get('http://news.sina.com.cn/', headers={'Accept-Encoding': 'deflate'}) as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            html = f.read()
            self.assertTrue(sina in html)

        with tempfile.TemporaryFile() as f:
            with urlfetch.get('http://news.sina.com.cn/', headers={'Accept-Encoding': 'gzip'}) as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            html = f.read()
            self.assertTrue(sina in html)

        with tempfile.TemporaryFile() as f:
            with urlfetch.get('http://news.sina.com.cn/', headers={'Accept-Encoding': '*'}) as r:
                for chunk in r:
                    f.write(chunk)
            f.seek(0)
            html = f.read()
            self.assertTrue(sina in html)

    def test_cookie(self):
        cookie = (randstr(), randstr())
        r = urlfetch.get(testlib.url('setcookie/%s/%s' % cookie))
        self.assertEqual(r.links, [])
        self.assertEqual(r.cookies[cookie[0]], cookie[1])
        self.assertTrue(('%s=%s' % cookie) in r.cookiestring)

    def test_redirect(self):
        r = urlfetch.get(testlib.url('/redirect/3/0'))
        self.assertTrue(r.status in (301, 302, 303, 307))
        self.assertEqual(r.links, [])
        self.assertTrue('location' in r.headers)

        self.assertRaises(urlfetch.UrlfetchException, lambda: urlfetch.get(testlib.url('/redirect/3/0'), max_redirects=1))
        self.assertRaises(urlfetch.UrlfetchException, lambda: urlfetch.get(testlib.url('/redirect/3/0'), max_redirects=2))

        r = urlfetch.get(testlib.url('/redirect/3/0'), max_redirects=3)
        o = r.json
        self.assertEqual(r.status, 200)
        self.assertEqual(len(r.history), 3)
        self.assertEqual(o['method'], 'GET')
        self.assertTrue('location' not in r.headers)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))

    def test_history(self):
        r = urlfetch.get(testlib.url('/redirect/5/0'), max_redirects=10)
        self.assertTrue(not not r.history)

        responses = r.history[:]
        responses.append(r)
        responses.reverse()

        for r1, r2 in zip(responses, responses[1:]):
            self.assertEqual(r1.history[:-1], r2.history)

    def test_content_encoding(self):
        url = testlib.url('/content-encoding/invalid-body')
        call_invalid_body = lambda: urlfetch.get(url).body
        self.assertRaises(urlfetch.ContentDecodingError, call_invalid_body)

        url = testlib.url('/content-encoding/invalid-header')
        call_invalid_header = lambda: urlfetch.get(url).body
        self.assertRaises(urlfetch.ContentDecodingError, call_invalid_header)

        url = testlib.url('/content-encoding/invalid-body/deflate')
        call_invalid_header_deflate = lambda: urlfetch.get(url).body
        self.assertRaises(urlfetch.ContentDecodingError, call_invalid_header_deflate)

    def length_limit(self):
        url = testlib.url('/bytes/64')
        call = lambda: urlfetch.get(url, length_limit=1)
        self.assertRaises(urlfetch.ContentLimitExceeded, call)
        call = lambda: urlfetch.get(url, length_limit=63)
        self.assertRaises(urlfetch.ContentLimitExceeded, call)

    def test_links(self):
        r = urlfetch.get(testlib.url('/links/0'))
        self.assertTrue(r.links)
        self.assertTrue(isinstance(r.links, list))
        self.assertTrue(len(r.links) == 1)

        r = urlfetch.get(testlib.url('/links/1'))
        self.assertTrue(r.links)
        self.assertTrue(isinstance(r.links, list))
        self.assertTrue(len(r.links) == 2)

        r = urlfetch.get(testlib.url('/links/2'))
        self.assertTrue(r.links)
        self.assertTrue(isinstance(r.links, list))
        self.assertTrue(len(r.links) == 4)

        r = urlfetch.get(testlib.url('/links/3'))
        self.assertTrue(r.links)
        self.assertTrue(isinstance(r.links, list))
        self.assertTrue(len(r.links) == 2)

        r = urlfetch.get(testlib.url('/links/none'))
        self.assertTrue(r.links)
        self.assertTrue(isinstance(r.links, list))
        self.assertTrue(len(r.links) == 1)

if __name__ == '__main__':
    unittest.main()
