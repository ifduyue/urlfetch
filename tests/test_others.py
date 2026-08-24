#coding: utf8
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


if __name__ == '__main__':
    unittest.main()
