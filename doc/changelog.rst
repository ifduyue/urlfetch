Changelog
===========

**Time flies!!**

1.0.2 (2015-04-29)
++++++++++++++++++++

Fixes:

* ``python setup.py test`` causes SandboxViolation.

Improvements:

* ``python setup.py test`` handles dependencies automatically.
* :func:`random_useragent`: check if ``urlfetch.useragents.list`` exists at
  the import time.

1.0.1 (2015-01-31)
++++++++++++++++++++

Fixes:

* :attr:`urlfetch.Response.history` of a redirected response and its
  precedent responses should be different.

Improvements:

* Simplified some code.
* Added some tests.

1.0 (2014-03-22)
++++++++++++++++++++

New features:

* Support idna.
* Assignable :attr:`.Session.cookiestring`.

Backwards-incompatible changes:

* Remove ``raw_header`` and ``raw_response``.
* :func:`random_useragent` now takes a single ``filename`` as parameter. It used to be a list of filenames.
* No more ``.title()`` on request headers' keys.
* Exceptions are re-designed. :class:`socket.timeout` now is :class:`.Timeout`, ..., see section `Exceptions` in :doc:`reference` for more details.

Fixes:

* Parsing links: If ``Link`` header is empty, ``[]`` should be returned, not ``[{'url': ''}]``.
* Http request's ``Host`` header should include the port. Using ``netloc`` as the http host header is wrong, it could include user:pass.
* Redirects: ``Host`` in reqheaders should be ``host:port``.
* Streaming decompress not working.


0.6.2 (2014-03-22)
++++++++++++++++++++

Fix:

* Http request's host header should include the port. Using ``netloc`` as the http host header is wrong, it could include user:pass.

0.6.1 (2014-03-15)
++++++++++++++++++++

Fix:

* Parsing links: If ``Link`` header is empty, ``[]`` should be returned, not ``[{'url': ''}]``.

0.6   (2013-08-26)
++++++++++++++++++++

Change:

* Remove lazy response introduced in 0.5.6
* Remove the dump, dumps, load and loads methods of :class:`urlfetch.Response`

0.5.7 (2013-07-08)
++++++++++++++++++++

Fix:

* Host header field should include host and port

0.5.6 (2013-07-04)
++++++++++++++++++++

Feature:

* Lay response. Read response when you need it.

0.5.5 (2013-06-07)
++++++++++++++++++++

Fix:

* fix docstring.
* parse_url raise exception for http://foo.com:/

0.5.4.2 (2013-03-31)
++++++++++++++++++++

Feature: 

* :attr:`urlfetch.Response.link`, links parsed from HTTP Link header.

Fix:

* Scheme doesn't correspond to the new location when following redirects.


0.5.4.1 (2013-03-05)
++++++++++++++++++++

Fix:

* :func:`urlfetch.random_useragent` raises exception ``[Errno 2] No such file or directory``.
* :func:`urlfetch.encode_multipart` doesn't use `isinstance: (object, class-or-type-or-tuple)` correctly.


0.5.4 (2013-02-28)
++++++++++++++++++++

Feature:

* HTTP Proxy-Authorization.

Fix:

* Fix docstring typos.
* :func:`urlfetch.encode_multipart` should behave the same as `urllib.urlencode(query, doseq=1)`.
* :func:`urlfetch.parse_url` should parse urls like they are HTTP urls.


0.5.3.1 (2013-02-01)
++++++++++++++++++++++

Fix:

*  :attr:`urlfetch.Response.content` becomes empty after the first access.

0.5.3 (2013-02-01)
+++++++++++++++++++

Feature:

* NEW :attr:`urlfetch.Response.status_code`, alias of :attr:`urlfetch.Response.status` .
* NEW :attr:`urlfetch.Response.total_time`, :attr:`urlfetch.Response.raw_header` and :attr:`urlfetch.Response.raw_response`.
* Several properties of :class:`urlfetch.Response` are cached to avoid unnecessary calls, including :attr:`urlfetch.Response.text`, :attr:`urlfetch.Response.json`, :attr:`urlfetch.Response.headers`, :attr:`urlfetch.Response.cookies`, :attr:`urlfetch.Response.cookiestring`, :attr:`urlfetch.Response.raw_header` and :attr:`urlfetch.Response.raw_response`.

Fix:

* :func:`urlfetch.mb_code` may silently return incorrect result, since the encode errors are replaced, it should be decode properly and then encode without replace.


0.5.2 (2012-12-24)
+++++++++++++++++++

Feature:

* :func:`~urlfetch.random_useragent` can accept list/tuple/set params and can accept more than one params which specify the paths to check and read from. Below are some examples::
    
    >>> ua = random_useragent('file1')
    >>> ua = random_useragent('file1', 'file2')
    >>> ua = random_useragent(['file1', 'file2'])
    >>> ua = random_useragent(['file1', 'file2'], 'file3')

Fix:

* Possible infinite loop in :func:`~urlfetch.random_useragent`.

0.5.1 (2012-12-05)
+++++++++++++++++++

Fix:

* In some platforms ``urlfetch.useragents.list`` located in wrong place.
* :func:`~urlfetch.random_useragent` will never return the first line.
* Typo in the description of urlfetch.useragents.list (the first line). 

0.5.0 (2012-08-23)
+++++++++++++++++++

* Redirects support. Parameter ``max_redirects`` specify the max redirects allowed within a request. Default is ``0``, which means redirects are not allowed.
* Code cleanups

0.4.3 (2012-08-17)
+++++++++++++++++++

* Add ``params`` parameter, ``params`` is dict or string to attach to request url as querysting.
* Gzip and deflate support.

0.4.2 (2012-07-31)
+++++++++++++++++++

* HTTP(S) proxies support.

0.4.1 (2012-07-04)
+++++++++++++++++++

* Streaming support.

0.4.0 (2012-07-01)
+++++++++++++++++++

* NEW :class:`urlfetch.Session` to manipulate cookies automatically, share common request headers and cookies.
* NEW :attr:`urlfetch.Response.cookies` and :attr:`urlfetch.Response.cookiestring` to get response cookie dict and cookie string.

0.3.6 (2012-06-08)
+++++++++++++++++++

* Simplify code
* Trace method without data and files, according to RFC2612
* ``urlencode(data, 1)`` so that ``urlencode({'param': [1,2,3]})`` => ``'param=1&param=2&param=3'``

0.3.5 (2012-04-24)
+++++++++++++++++++

* Support specifying an IP for the request host, useful for testing API.

0.3.0 (2012-02-28)
+++++++++++++++++++

* Python 3 compatible

0.2.2 (2012-02-22)
+++++++++++++++++++
* Fix bug: file upload: file should always have a filename

0.2.1 (2012-02-22) 
+++++++++++++++++++

* More flexible file upload
* Rename fetch2 to request
* Add auth parameter, instead of put basic authentication info in url

0.1.2 (2011-12-07)
+++++++++++++++++++

* Support basic auth

0.1 (2011-12-02)
+++++++++++++++++++

* First release
