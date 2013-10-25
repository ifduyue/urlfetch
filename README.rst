urlfetch
========

.. |travis-ci-image| image:: https://travis-ci.org/ifduyue/urlfetch.png
.. _travis-ci-image: https://travis-ci.org/ifduyue/urlfetch

|travis-ci-image|_

urlfetch is a simple, lightweigth and easy to use HTTP client for Python. 
It is distributed as a single file module and has no depencencies other than the Python Standard Library.

Installation
-------------
::
    
    $ pip install urlfetch --upgrade


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

