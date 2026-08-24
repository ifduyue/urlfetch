import socket
import ssl
import unittest
from unittest import mock

import testlib
import urlfetch


class ProxyTest(unittest.TestCase):

    def test_get_via_proxy(self):
        proxy = testlib.test_server_host[:-1]
        resp = urlfetch.get('http://www.example.com', proxies={'http':proxy})
        self.assertEqual(resp.status, 200)
        self.assertTrue(isinstance(resp.json, dict))
        self.assertTrue(isinstance(resp.text, str))

        proxy = proxy.split('://', 1)[1]
        resp = urlfetch.get('http://www.example.com', proxies={'http':proxy})
        self.assertEqual(resp.status, 200)
        self.assertTrue(isinstance(resp.json, dict))
        self.assertTrue(isinstance(resp.text, str))

    def test_https_proxy_uses_connect(self):
        seen = {}

        class BoomHTTPSConnection(urlfetch.HTTPSConnection):
            def set_tunnel(self, host, port=None, headers=None):
                seen['host'] = host
                seen['port'] = port
                seen['headers'] = headers
                raise socket.error('stop')

        with mock.patch('urlfetch.HTTPSConnection', BoomHTTPSConnection):
            self.assertRaises(
                urlfetch.UrlfetchException,
                lambda: urlfetch.get(
                    'https://example.com/path',
                    proxies={'https': 'http://user:secret@127.0.0.1:8888'},
                ),
            )
        self.assertEqual(seen['host'], 'example.com')
        self.assertEqual(seen['port'], 443)
        self.assertIn('Proxy-Authorization', seen['headers'])

    def test_ssl_context_passed_through(self):
        ctx = ssl._create_unverified_context()
        seen = {}

        class Rec(urlfetch.HTTPSConnection):
            def __init__(self, *args, **kwargs):
                seen['context'] = kwargs.get('context')
                raise socket.error('stop')

        with mock.patch('urlfetch.HTTPSConnection', Rec):
            self.assertRaises(
                urlfetch.UrlfetchException,
                lambda: urlfetch.get('https://example.com/', ssl_context=ctx),
            )
        self.assertIs(seen['context'], ctx)


if __name__ == '__main__':
    unittest.main()
