import testlib
import urlfetch

import unittest
import json
import random
import socket
import os


class GetTest(unittest.TestCase):
    
    def test_session(self):
        headers = testlib.randdict()
        cookies = testlib.randdict()
        s = urlfetch.Session(headers=headers, cookies=cookies)
        
        headers = dict((k.title(), v) for k, v in headers.items())
        self.assertEqual(s.snapshot(), {'headers': headers, 'cookies': cookies})
        
        randstr = testlib.randstr
        
        header = (randstr(), randstr())
        headers[header[0].title()] = header[1]
        s.putheader(*header)
        self.assertEqual(s.snapshot(), {'headers': headers, 'cookies': cookies})
        
        cookie = (randstr(), randstr())
        cookies[cookie[0]] = cookie[1]
        s.putcookie(*cookie)
        self.assertEqual(s.snapshot(), {'headers': headers, 'cookies': cookies})
        
        header = headers.popitem()
        s.popheader(header[0])
        self.assertEqual(s.snapshot(), {'headers': headers, 'cookies': cookies})
        
        cookie = cookies.popitem()
        s.popcookie(cookie[0])
        self.assertEqual(s.snapshot(), {'headers': headers, 'cookies': cookies})
        
        s = urlfetch.Session()
        cookie = (randstr(), randstr())
        r = s.get(testlib.test_server_host + 'setcookie/%s/%s' % cookie)
        self.assertEqual(s.cookies[cookie[0]], cookie[1])

        cookie2 = (randstr(), randstr())
        r = s.get(testlib.test_server_host + 'setcookie/%s/%s' % cookie2)
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookie))
        self.assertEqual(s.cookies[cookie[0]], cookie[1])
        self.assertEqual(s.cookies[cookie2[0]], cookie2[1])
        

    def test_session_fetch(self):
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)))
        r = s.fetch(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))

    def test_session_get(self):
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)))
        r = s.get(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        
    def test_session_fragment(self):
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)))
        r = s.get(testlib.test_server_host + '#urlfetch')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))

    def test_session_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)))
        r = s.get(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        
        r = s.get(testlib.test_server_host + '?' + query_string)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)
        
    def test_session_fragment_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)))
        r = s.get(testlib.test_server_host)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        
        r = s.get(testlib.test_server_host + '?' + query_string + '#urlfetch')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_session_basic_auth(self):
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)), auth=('urlfetch', 'fetchurl'))
        r = s.get(testlib.test_server_host + 'basic_auth')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        
    def test_session_fragment_basic_auth(self):
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)), auth=('urlfetch', 'fetchurl'))
        r = s.get(testlib.test_server_host + 'basic_auth#urlfetch')
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))

    def test_session_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)), auth=('urlfetch', 'fetchurl'))
        r = s.get(testlib.test_server_host + 'basic_auth?' + query_string)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)
        
    def test_session_fragment_basic_auth_query_string(self):
        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)
        
        cookiepair = (testlib.randstr(), testlib.randstr())
        headerpair = (testlib.randstr(), testlib.randstr())
        s = urlfetch.Session(headers=dict((headerpair,)), cookies=dict((cookiepair,)), auth=('urlfetch', 'fetchurl'))
        r = s.get(testlib.test_server_host + 'basic_auth?' + query_string + '#urlfetch')
        o = json.loads(r.text)
        
        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(r.reqheaders[headerpair[0].title()], headerpair[1])
        self.assertEqual(r.reqheaders['Cookie'], '='.join(cookiepair))
        self.assertEqual(o['query_string'], query_string)
        self.assertEqual(o['get'], qs)

    def test_timeout(self):
        self.assertRaises(socket.timeout, lambda:urlfetch.Session().get(testlib.test_server_host + 'sleep/1', timeout=0.5))


if __name__ == '__main__':
    unittest.main()
