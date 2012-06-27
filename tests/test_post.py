import testlib
from testlib import py3k
import urlfetch

import unittest
import json
import random


class PostTest(unittest.TestCase):

    def test_fetch(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        r = urlfetch.fetch(testlib.test_server_host, data=data)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)

    def test_post(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        r = urlfetch.post(testlib.test_server_host, data=data)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)

    def test_post_query_string(self):
        d = testlib.randdict()
        data = urlfetch.urlencode(d)

        qs = testlib.randdict(5)
        query_string = urlfetch.urlencode(qs)

        r = urlfetch.post(testlib.test_server_host + '?'+query_string, data=data)
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(o['post'], d)
        self.assertEqual(o['get'], qs)
        self.assertEqual(o['query_string'], query_string)

    def test_file_upload(self):
        content = open('test.file', 'rb').read()
        files = {}
        files['test.file1'] = (b'test.file1', b'test.file', content)
        #files[b'test.file2'] = (b'test.file2', b'', content)
        files['test.file3'] = (b'test.file3', b'wangxiaobo', content)
        files['test.file4'] = (b'test.file4', b'wangtwo', content)

        r = urlfetch.post(
                testlib.test_server_host,
                files = {
                    'test.file1' : open('test.file'),
                    #'test.file2' : content,
                    'test.file3' : ('wangxiaobo', open('test.file')),
                    'test.file4' : ('wangtwo', content)
                },
            )
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(sorted(o['files'].keys()), sorted(files.keys()))

        for i in files:
            for j in range(3):
                self.assertEqual(o['files'][i][j].encode('utf-8'), files[i][j])


    def test_one_file_upload(self):
        content = open('test.file', 'rb').read()
        files = {'test.file': (b'test.file', b'test.file', content)}

        r = urlfetch.post(
                testlib.test_server_host,
                files = {
                    'test.file' : ('test.file', content),
                },
            )
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(sorted(o['files'].keys()), sorted(files.keys()))
        for i in files:
            for j in range(3):
                self.assertEqual(o['files'][i][j].encode('utf8'), files[i][j])

    def test_one_file_upload_gbk(self):
        content = open('test.file.gbk', 'rb').read()
        files = {'test.file': (b'test.file', b'test.file', content)}

        r = urlfetch.post(
                testlib.test_server_host,
                files = {
                    'test.file' : ('test.file', content),
                },
            )
        o = json.loads(r.text)

        self.assertEqual(r.status, 200)
        self.assertEqual(o['method'], 'POST')
        self.assertEqual(sorted(o['files'].keys()), sorted(files.keys()))
        for i in files:
            for j in range(3):
                self.assertEqual(o['files'][i][j].encode('gb2312'), files[i][j])

if __name__ == '__main__':
    unittest.main()
