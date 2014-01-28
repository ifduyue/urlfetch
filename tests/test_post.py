import testlib
from testlib import md5sum
import urlfetch

import unittest
import json


import os
here = os.path.dirname(os.path.abspath(__file__))
path = lambda *p: os.path.join(here, *p)

class PostTest(unittest.TestCase):

    def test_fetch(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        r = urlfetch.fetch(testlib.test_server_host, data=data)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)

    def test_post(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        r = urlfetch.post(testlib.test_server_host, data=data)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)

    def test_post_query_string(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)

        r = urlfetch.post(testlib.url('?' + query_string), data=data)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)
        self.assertEqual(o['get'], qs)
        self.assertEqual(o['query_string'], query_string)

    def test_file_upload(self):
        content = open(path('test.file'), 'rb').read()
        files = {}
        files['test.file1'] = (b'test.file1', b'test.file', content)
        #files[b'test.file2'] = (b'test.file2', b'', content)
        files['test.file3'] = (b'test.file3', b'wangxiaobo', content)
        files['test.file4'] = (b'test.file4', b'wangtwo', content)

        r = urlfetch.post(
                testlib.test_server_host,
                files = {
                    'test.file1' : open(path('test.file')),
                    #'test.file2' : content,
                    'test.file3' : ('wangxiaobo', open(path('test.file'))),
                    'test.file4' : ('wangtwo', content)
                },
            )
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(sorted(o['files'].keys()), sorted(files.keys()))

        for i in files:
            self.assertEqual(o['files'][i][0].encode('utf-8'), files[i][0])
            self.assertEqual(o['files'][i][1].encode('utf-8'), files[i][1])
            self.assertEqual(o['files'][i][2].encode('utf-8'), md5sum(files[i][2]))

    def test_file_upload_multipart(self):
        content = open(path('test.file'), 'rb').read()
        files = {}
        files['test.file1'] = (b'test.file1', b'test.file', content)
        #files[b'test.file2'] = (b'test.file2', b'', content)
        files['test.file3'] = (b'test.file3', b'wangxiaobo', content)
        files['test.file4'] = (b'test.file4', b'wangtwo', content)
        data = testlib.randdict()
        params = testlib.randdict(5)

        r = urlfetch.post(
                testlib.test_server_host,
                data = data,
                params = params,
                files = {
                    'test.file1' : open(path('test.file')),
                    #'test.file2' : content,
                    'test.file3' : ('wangxiaobo', open(path('test.file'))),
                    'test.file4' : ('wangtwo', content)
                },
            )
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], data)
        self.assertEqual(sorted(o['files'].keys()), sorted(files.keys()))

        for i in files:
            self.assertEqual(o['files'][i][0].encode('utf-8'), files[i][0])
            self.assertEqual(o['files'][i][1].encode('utf-8'), files[i][1])
            self.assertEqual(o['files'][i][2].encode('utf-8'), md5sum(files[i][2]))

        for k, v in params.items():
            self.assertTrue(('%s=%s' % (k, v)) in r.url)

    def test_one_file_upload(self):
        content = open(path('test.file'), 'rb').read()
        files = {'test.file': (b'test.file', b'test.file', content)}

        r = urlfetch.post(
                testlib.test_server_host,
                files = {
                    'test.file' : ('test.file', content),
                },
            )
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(sorted(o['files'].keys()), sorted(files.keys()))
        for i in files:
            self.assertEqual(o['files'][i][0].encode('utf8'), files[i][0])
            self.assertEqual(o['files'][i][1].encode('utf8'), files[i][1])
            self.assertEqual(o['files'][i][2].encode('utf8'), md5sum(files[i][2]))

    def test_one_file_upload_gbk(self):
        content = open(path('test.file.gbk'), 'rb').read()
        files = {'test.file': (b'test.file', b'test.file', content)}

        r = urlfetch.post(
                testlib.test_server_host,
                files = {
                    'test.file' : ('test.file', content),
                },
            )
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertTrue(isinstance(r.json, dict))
        self.assertTrue(isinstance(r.text, urlfetch.unicode))
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(sorted(o['files'].keys()), sorted(files.keys()))
        for i in files:
            self.assertEqual(o['files'][i][0].encode('gbk'), files[i][0])
            self.assertEqual(o['files'][i][1].encode('gbk'), files[i][1])
            self.assertEqual(o['files'][i][2].encode('gbk'), md5sum(files[i][2]))


if __name__ == '__main__':
    unittest.main()
