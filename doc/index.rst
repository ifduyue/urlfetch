.. highlight:: python
.. currentmodule:: urlfetch

======================
urlfetch documentation
======================

urlfetch is a simple, lightweight and easy to use HTTP client for `Python <http://python.org/>`_.
It is distributed as a single file module and has no depencencies other than the
`Python Standard Library <http://docs.python.org/library/>`_.


Getting Started
================

Install
------------

::
    
    $ pip install urlfetch --upgrade
    
OR::

    $ easy_install urlfetch --upgrade

OR grab the latest source from github
`ifduyue/urlfetch <https://github.com/ifduyue/urlfetch>`_::
    
    $ git clone git://github.com/ifduyue/urlfetch.git
    $ cd urlfetch
    $ python setup.py install
    

Usage
------

>>> import urlfetch
>>> r = urlfetch.get("http://docs.python.org/")
>>> r.status, r.reason
(200, 'OK')
>>> r.getheader('content-type')
'text/html; charset=UTF-8'
>>> r.getheader('Content-Type')
'text/html; charset=UTF-8'
>>> r.content
...

    
User's Guide
=============

.. toctree::
    
    examples
    reference
    changelog
    contributors

License
=========

Code and documentation are available according to the BSD 2-clause License:

.. include:: ../LICENSE
    :literal:
