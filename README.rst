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

urlfetch is a simple, lightweight and easy to use HTTP client for Python. 
It is distributed as a single file module and has no depencencies other than the Python Standard Library.

Installation
-------------
::
    
    $ pip install urlfetch


Hello World
-----------
::
    
    from urlfetch import get
    
    response = get('http://python.org/')
    print response.content

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



.. image:: https://d2weczhvl823v0.cloudfront.net/ifduyue/urlfetch/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free

