urlfetch
========

Description
-----------
An easy to use HTTP client.

Installation
-------------
::
    
    $ pip install urlfetch -U


Hello World
-----------
::
    
    from urlfetch import get
    
    response = get('http://python.org/')
    print response.body

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

    print response.status, response.body

