urlfetch
========

Description
-----------
An easy to use HTTP client based on httplib

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
    response = post('http://127.0.0.1:8888/', files={'formname': open('/path/to/file', 'rb')})
    print response.reqheaders
    print response.body
