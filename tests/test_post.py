import unittest
import urlfetch
import json
import random

import testlib

class PostTest(unittest.TestCase):

    def test_fetch(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        r = urlfetch.fetch('http://127.0.0.1:8800/', data=data)
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)

    def test_post(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        r = urlfetch.post('http://127.0.0.1:8800/', data=data)
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)

    def test_post_query_string(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)

        r = urlfetch.post('http://127.0.0.1:8800/?'+query_string, data=data)
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)
        self.assertEqual(o['get'], qs)
        self.assertEqual(o['query_string'], query_string)

    def test_file_upload(self):
        content = open('test.file', 'rb').read()
        files = {}
        files['test.file1'] = ('test.file1', 'test.file', content)
        #files['test.file2'] = ('test.file2', '', content)
        files['test.file3'] = ('test.file3', 'wangxiaobo', content)
        files['test.file4'] = ('test.file4', 'wangtwo', content)

        r = urlfetch.post(
                'http://127.0.0.1:8800/',
                files = {
                    'test.file1' : open('test.file'),
                    #'test.file2' : content,
                    'test.file3' : ('wangxiaobo', open('test.file')),
                    'test.file4' : ('wangtwo', content)
                },
            )
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertItemsEqual(o['files'].keys(), files.keys())
        for i in files:
            for j in xrange(3):
                self.assertEqual(o['files'][i][j], files[i][j].decode('utf-8'))


    def test_one_file_upload(self):
        content = open('test.file', 'rb').read()
        files = {'test.file': ('test.file', 'test.file', content)}

        r = urlfetch.post(
                'http://127.0.0.1:8800/',
                files = {
                    'test.file' : ('test.file', content),
                },
            )
        o = json.loads(r.body)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertItemsEqual(o['files'].keys(), files.keys())
        for i in files:
            for j in xrange(3):
                self.assertEqual(o['files'][i][j], files[i][j].decode('utf-8'))

if __name__ == '__main__':
    unittest.main()
