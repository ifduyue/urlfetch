.. highlight:: python

.. _httplib: http://docs.python.org/library/httplib.html?highlight=httplib#module-httplib
.. _Python: http://python.org/


======================
urlfetch documentation
======================


Introduction
=============
urlfetch is an easy to use HTTP client based on Python_ httplib_ module.

Examples
=========
.. rubric:: get http://python.org/ content 

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

.. autofunction:: fetch2

.. autofunction:: sc2cs

.. autofunction:: randua
