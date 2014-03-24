urlfetch
========

.. image:: https://travis-ci.org/ifduyue/urlfetch.png
    :target: https://travis-ci.org/ifduyue/urlfetch

.. image:: https://coveralls.io/repos/ifduyue/urlfetch/badge.png?branch=master
    :target: https://coveralls.io/r/ifduyue/urlfetch?branch=master

.. image:: https://badge.fury.io/py/urlfetch.png
    :target: http://badge.fury.io/py/urlfetch

.. image:: https://pypip.in/d/urlfetch/badge.png
    :target: https://crate.io/packages/urlfetch/

.. image:: https://d2weczhvl823v0.cloudfront.net/ifduyue/urlfetch/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free

urlfetch is a simple, lightweight and easy to use HTTP client for Python.
It is distributed as a single file module and has no depencencies other than the Python Standard Library.


Highlights
-------------

* Distributed as a single file module, has no depencencies other than the Python Standard Library.
* Pure Python, works fine with gevent_.
* Small codebase, about 1000 lines and 30% are comments and blank lines. Only 10 minutes you can know every detail.
* Random user-agent.
* Support streaming.

.. _gevent: http://www.gevent.org/

Installation
-------------
::

    $ pip install urlfetch


Hello, world
-------------
::

    from urlfetch import get

    response = get('http://python.org/')
    print response.status, response.reason
    print len(response.content)

Upload file
-----------
::

    from urlfetch import post

    response = post(
        'http://127.0.0.1:8888/upload',
        headers = {
            'Referer': 'http://127.0.0.1/',
        },
        files = {
            'fieldname1': open('/path/to/file', 'rb'),
            #'fieldname2': 'file content', # file must have a filename
            'fieldname3': ('filename', open('/path/to/file2', 'rb')),
            'fieldname4': ('filename', 'file content'),
        },
        data = {
            'foo': 'bar'
        },
    )

    print response.status, response.content

