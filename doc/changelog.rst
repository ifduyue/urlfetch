Changelog
===========

**Time flies!!**

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
