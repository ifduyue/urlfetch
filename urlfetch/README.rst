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

