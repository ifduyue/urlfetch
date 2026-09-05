urlfetch |github-actions-badge| |furyio-badge| |docs-badge|
============================================================

.. |github-actions-badge| image:: https://github.com/ifduyue/urlfetch/actions/workflows/test.yml/badge.svg
    :target: https://github.com/ifduyue/urlfetch/actions/workflows/test.yml

.. |furyio-badge| image:: https://badge.fury.io/gh/ifduyue%2Furlfetch.svg
    :target: https://badge.fury.io/gh/ifduyue%2Furlfetch

.. |docs-badge| image:: https://img.shields.io/badge/docs-GitHub%20Pages-blue
    :target: https://ifduyue.github.io/urlfetch/

urlfetch is a simple, lightweight and easy to use HTTP client for Python.
It is distributed as a single file module and has no dependencies other than the Python Standard Library.


Highlights
-------------

* Distributed as a single file module, has no dependencies other than the Python Standard Library.
* Pure Python, works fine with gevent_.
* Small codebase, about 1300 lines, much of it comments and blank lines. Only 10 minutes you can know every detail.
* Random user-agent.
* Support streaming.

.. _gevent: http://www.gevent.org/

Documentation
-------------

https://ifduyue.github.io/urlfetch/


Installation
-------------
::

    $ pip install urlfetch


Hello, world
-------------

.. code-block:: python

    import urlfetch

    response = urlfetch.get('http://python.org/')
    print(response.status, response.reason)
    print(len(response.content))

Uploading files
----------------

.. code-block:: python

    import urlfetch

    response = urlfetch.post(
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

    print(response.status, response.content)


Testing
--------

.. __: http://bottlepy.org/
.. __: http://gunicorn.org/

To run the tests, urlfetch relies on `bottle`__ and `gunicorn`__.
Install them and run::

    $ python tests/testall.py


