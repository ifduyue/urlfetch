import testlib
import urlfetch
import unittest


class ProxyTest(unittest.TestCase):

    def test_get_via_proxy(self):
        proxy = testlib.test_server_host[:-1]
        resp = urlfetch.get('http://www.example.com', proxies={'http':proxy})
        self.assertEqual(resp.status, 200)
        self.assertTrue(isinstance(resp.json, dict))
        self.assertTrue(isinstance(resp.text, urlfetch.unicode))

        proxy = proxy.split('://', 1)[1]
        resp = urlfetch.get('http://www.example.com', proxies={'http':proxy})
        self.assertEqual(resp.status, 200)
        self.assertTrue(isinstance(resp.json, dict))
        self.assertTrue(isinstance(resp.text, urlfetch.unicode))


if __name__ == '__main__':
    unittest.main()
