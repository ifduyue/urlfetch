import testlib
import urlfetch
import unittest


class ProxyTest(unittest.TestCase):

    def test_get_via_proxy(self):
        resp = urlfetch.get('http://www.example.com', proxies={'http':testlib.test_server_host})
        print resp


if __name__ == '__main__':
    unittest.main()
