#coding: utf8
import urlfetch
import unittest


class HelpersTest(unittest.TestCase):

    def test_cached_property(self):

        class Foo:
            def __init__(self):
                self.calls = 0

            @property
            def normal(self):
                self.calls += 1
                return self.calls

            @urlfetch.cached_property
            def cached(self):
                self.calls += 1
                return self.calls

        foo = Foo()

        self.assertEqual(foo.calls, 0)
        self.assertEqual(foo.cached, 1)
        self.assertEqual(foo.cached, 1)
        self.assertEqual(foo.normal, 2)
        self.assertEqual(foo.normal, 3)
        self.assertTrue(isinstance(Foo.cached, urlfetch.cached_property))

    def test_parse_url(self):
        url = 'http://www.example.com'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['scheme'], 'http')
        self.assertEqual(parsed_url['netloc'], 'www.example.com')
        self.assertEqual(parsed_url['host'], 'www.example.com')

        url = 'http://www.example.com:8800'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['scheme'], 'http')
        self.assertEqual(parsed_url['host'], 'www.example.com')
        self.assertEqual(parsed_url['port'], 8800)

        url = 'https://www.example.com'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['scheme'], 'https')

        url = 'http://www.example.com/path'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['path'], '/path')

        url = 'http://www.example.com/path?key1=value1&key2=value2'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['path'], '/path')
        self.assertEqual(parsed_url['query'], 'key1=value1&key2=value2')

        url = 'http://www.example.com/path?key1=value1&key2=value2#fragment'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['path'], '/path')
        self.assertEqual(parsed_url['query'], 'key1=value1&key2=value2')
        self.assertEqual(parsed_url['fragment'], 'fragment')

        url = 'https://username:password@www.example.com'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['scheme'], 'https')
        self.assertEqual(parsed_url['username'], 'username')
        self.assertEqual(parsed_url['password'], 'password')

        url = 'https://username:password@www.example.com:-'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['scheme'], 'https')
        self.assertEqual(parsed_url['username'], 'username')
        self.assertEqual(parsed_url['password'], 'password')
        self.assertEqual(parsed_url['port'], None)

        url = 'http://www.example.com/?中国'
        self.assertEqual(not not urlfetch.parse_url(url), True)
        url = 'http://www.example.中国/?中国'
        self.assertEqual(not not urlfetch.parse_url(url), True)

        url = 'http://[::1]:8080/path'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['host'], '::1')
        self.assertEqual(parsed_url['port'], 8080)
        self.assertEqual(parsed_url['http_host'], '[::1]:8080')
        self.assertEqual(parsed_url['path'], '/path')

        url = 'http://[2001:db8::1]/'
        parsed_url = urlfetch.parse_url(url)
        self.assertEqual(parsed_url['host'], '2001:db8::1')
        self.assertEqual(parsed_url['http_host'], '[2001:db8::1]')

    def test_random_useragent(self):
        ua = urlfetch.random_useragent()
        self.assertTrue(isinstance(ua, (str, bytes)))
        self.assertTrue(len(ua) > 0)
        self.assertNotEqual(ua[0], '#')

    def test_choose_boundary(self):
        a = urlfetch.choose_boundary()
        b = urlfetch.choose_boundary()
        self.assertNotEqual(a, b)
        self.assertEqual(len(a), len(b))

    def test_url_concat(self):
        self.assertEqual(urlfetch.url_concat("foo?a=b", dict(c="d")), 'foo?a=b&c=d')
        self.assertEqual(urlfetch.url_concat("foo?c=b", dict(c="d"), keep_existing=True), 'foo?c=b&c=d')
        self.assertEqual(urlfetch.url_concat("foo?c=b", dict(c="d"), keep_existing=False), 'foo?c=d')
        self.assertEqual(urlfetch.url_concat("foo?c=b", dict(c="d"), keep_existing=True), 'foo?c=b&c=d')
        self.assertEqual(urlfetch.url_concat('a', dict(b=[1,2,3])), 'a?b=1&b=2&b=3')
        self.assertEqual(urlfetch.url_concat('a?a=1&b=x', dict(b=[1,2,3])), 'a?a=1&b=x&b=1&b=2&b=3')

    def test_multipart_quotes_special_names(self):
        content_type, body = urlfetch.encode_multipart(
            {'say "hi"': 'ok'},
            {'file': ('weird"name.txt', b'data')},
        )
        self.assertIn(b'name="say \\"hi\\""', body)
        self.assertIn(b'filename="weird\\"name.txt"', body)
        self.assertIn(b'Content-Type: text/plain', body)

        content_type, body = urlfetch.encode_multipart(
            {},
            {'pic': ('x.png', b'data', 'image/png')},
        )
        self.assertIn(b'Content-Type: image/png', body)

    def test_match_no_proxy(self):
        m = urlfetch.match_no_proxy
        self.assertTrue(m('example.com', 'example.com'))
        self.assertTrue(m('foo.example.com', 'example.com'))
        self.assertTrue(m('foo.example.com', '.example.com'))
        self.assertFalse(m('notexample.com', 'example.com'))
        self.assertFalse(m('example.com.org', 'example.com'))
        self.assertTrue(m('localhost', 'localhost'))
        self.assertTrue(m('anything.test', '*'))

        self.assertTrue(m('192.168.1.1', '192.168.1.1'))
        self.assertTrue(m('192.168.1.50', '192.168.1.0/24'))
        self.assertFalse(m('10.0.0.1', '192.168.0.0/16'))
        self.assertTrue(m('192.168.1.1', '192.168.1.1:8080'))

        self.assertTrue(m('::1', '::1'))
        self.assertTrue(m('[::1]', '::1'))
        self.assertTrue(m('::1', '[::1]'))
        self.assertTrue(m('2001:db8::1', '2001:db8::/32'))
        self.assertFalse(m('fe80::1', '::1'))
        self.assertTrue(m('::1', '[::1]:8080'))


if __name__ == '__main__':
    unittest.main()
