.. highlight:: python

.. _httplib: http://docs.python.org/library/httplib.html?highlight=httplib#module-httplib
.. _Python: http://python.org/


======================
urlfetch documentation
======================


Introduction
=============
urlfetch is an easy to use HTTP client.

Installation
=============
::
    
    $ pip install urlfetch -U
    
OR::

    $ easy_install urlfetch -U

OR grab the source from `github lyxint/urlfetch <https://github.com/lyxint/urlfetch>`_::
    
    $ git clone git://github.com/lyxint/urlfetch.git
    $ cd urlfetch
    $ python setup.py install

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
            'fieldname3': ('filename', open('/path/to/file2', 'rb')),
            'fieldname4': ('filename', 'file content'),
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

.. autoclass:: Response
    :members:

.. autoclass:: Session
    :members:

.. autofunction:: fetch

.. autofunction:: request

.. autofunction:: get

.. autofunction:: post

.. autofunction:: head

.. autofunction:: put

.. autofunction:: delete

.. autofunction:: options

.. autofunction:: trace

.. autofunction:: patch

helpers
~~~~~~~~~~~

.. autofunction:: sc2cs

.. autofunction:: random_useragent

.. autofunction:: mb_code
