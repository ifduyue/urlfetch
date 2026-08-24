#coding: utf8
import testlib
import urlfetch
import unittest


class OthersTest(unittest.TestCase):

    def test_module_has_methods(self):
        for method in ('get', 'head', 'put', 'post', 'delete',
                       'options', 'trace', 'patch'):
            self.assertTrue(hasattr(urlfetch, method))
            self.assertTrue(callable(getattr(urlfetch, method)))

    def test_timeout_is_public(self):
        self.assertIn('Timeout', urlfetch.__all__)
        self.assertTrue(issubclass(urlfetch.Timeout, urlfetch.UrlfetchException))

    def test_ok_and_raise_for_status(self):
        r = urlfetch.get(testlib.url())
        self.assertTrue(r.ok)
        r.raise_for_status()

        r = urlfetch.get(testlib.url('status/404'))
        self.assertEqual(r.status, 404)
        self.assertFalse(r.ok)
        try:
            r.raise_for_status()
        except urlfetch.HTTPError as e:
            self.assertEqual(e.status, 404)
            self.assertIs(e.response, r)
        else:
            self.fail('HTTPError not raised')


if __name__ == '__main__':
    unittest.main()
