.. highlight:: python

.. _httplib: http://docs.python.org/library/httplib.html?highlight=httplib#module-httplib
.. _Python: http://python.org/


======================
urlfetch documentation
======================


Introduction
=============
urlfetch is an easy to use HTTP client based on Python_ httplib_ module.

Installation
=============
::
    
    $ pip install urlfetch -U
    
OR::

    $ easy_install urlfetch -U

Examples
=========
.. rubric:: get http://python.org/

::

    from urlfetch import fetch

    response = fetch("http://python.org")
    print response.body


.. rubric:: add specific HTTP headers

::

    from urlfetch import fetch

    response = fetch(
        "http://python.org",
        headers = {
            'User-Agent': 'urlfetch',
        }
    )
    print 'content length', response.body
    print 'request headers', response.reqheaders
    print 'response headers', response.getheaders()

.. rubric:: post data

::

    from urlfetch import fetch
    response = fetch(
        "http://python.org",
        data = {
            'foo': 'bar',
        }
    )
    print response.status
    
    
.. rubric:: Upload file

::

    from urlfetch import post

    response = post(
        'http://127.0.0.1:8888/upload', 
        headers = {
            'Referer': 'http://127.0.0.1/',
        },
        files = {
            'fieldname1': open('/path/to/file', 'rb'),
            'fieldname3': ('formname', open('/path/to/file2', 'rb')),
            'fieldname4': ('formname', 'file content'),
        },
        data = {
            'foo': 'bar'
        },
    )

    print response.status, response.body
    
.. rubric:: more complex: login to http://fanfou.com/ and publish a status

::

    #coding: utf8

    import urlfetch
    import re

    def pub2fanfou(username, password, status):
        #获取表单token
        response = urlfetch.fetch(
            "http://m.fanfou.com/"
        )
        token = re.search('''name="token".*?value="(.*?)"''', response.body).group(1)
        
        #登录
        response = urlfetch.fetch(
            "http://m.fanfou.com/",
            data = {
                'loginname': username,
                'loginpass': password,
                'action': 'login',
                'token': token,
                'auto_login': 'on',
            },
            headers = {
                "Referer": "http://m.fanfou.com/",
            }
        )
        
        #cookies
        cookies = urlfetch.sc2cs(response.getheader('Set-Cookie'))
        print cookies
        
        #获取表单token
        response = urlfetch.fetch(
            "http://m.fanfou.com/home",
            headers = {
                'Cookie': cookies,
                'Referer': "http://m.fanfou.com/home",
            }
        )
        token = re.search('''name="token".*?value="(.*?)"''', response.body).group(1)
        
        #发布状态
        response = urlfetch.fetch(
            "http://m.fanfou.com/",
            data = {
                'content': status,
                'token': token,
                'action': 'msg.post',
            },
            headers = {
                'Cookie': cookies,
                'Referer': "http://m.fanfou.com/home",
            }
        )

    if __name__ == '__main__':
        import sys
        pub2fanfou(*sys.argv[1:4])


Reference
==========

.. module:: urlfetch
   :platform: Unix, Windows
   :synopsis: HTTP Client
.. moduleauthor:: Elyes Du <lyxint@gmail.com>

.. autofunction:: fetch

.. note::

    You can use get, post, head, put, delete in a convenience way.
    
    fetch is equavalent to post if data is specified else get.

.. autofunction:: request

.. autofunction:: sc2cs

.. autofunction:: randua
