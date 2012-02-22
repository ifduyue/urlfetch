import unittest
import urlfetch
import json

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



if __name__ == '__main__':
    unittest.main()
