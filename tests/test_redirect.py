import unittest

import testlib
import urlfetch


class RedirectTest(unittest.TestCase):

    def test_post_becomes_get_on_302(self):
        r = urlfetch.post(
            testlib.url('redirect-status/302'),
            data={'foo': 'bar'},
            max_redirects=1,
        )
        o = r.json
        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'GET')
        self.assertEqual(o.get('post') or {}, {})
        self.assertNotIn('Content-Type', r.reqheaders)

    def test_307_preserves_post(self):
        r = urlfetch.post(
            testlib.url('redirect-status/307'),
            data={'foo': 'bar'},
            max_redirects=1,
        )
        o = r.json
        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], {'foo': 'bar'})

    def test_308_preserves_post(self):
        r = urlfetch.post(
            testlib.url('redirect-status/308'),
            data={'foo': 'bar'},
            max_redirects=1,
        )
        o = r.json
        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], {'foo': 'bar'})

    def test_same_origin_keeps_authorization(self):
        r = urlfetch.get(
            testlib.url('redirect/1/0'),
            auth=('urlfetch', 'fetchurl'),
            max_redirects=2,
        )
        self.assertEqual(r.status, 200)
        self.assertTrue(r.reqheaders.get('Authorization', '').startswith('Basic '))

    def test_cross_host_strips_authorization(self):
        r = urlfetch.get(
            testlib.url('redirect-cross-host'),
            auth=('urlfetch', 'fetchurl'),
            max_redirects=1,
        )
        self.assertEqual(r.status, 200)
        self.assertNotIn('Authorization', r.reqheaders)


if __name__ == '__main__':
    unittest.main()
