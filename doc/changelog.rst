Changelog
===========

**Time flies!!**

0.4.3 (2012-08-17)
+++++++++++++++++++

* add ``params`` parameter, ``params`` is dict or string to attach to request url as querysting.
* gzip and deflate support.

0.4.2 (2012-07-31)
+++++++++++++++++++

* HTTP(S) proxies support.

0.4.1 (2012-07-04)
+++++++++++++++++++

* streaming support.

0.4.0 (2012-07-01)
+++++++++++++++++++

* NEW :class:`urlfetch.Session` to manipulate cookies automatically, share common request headers and cookies.
* NEW :attr:`urlfetch.Response.cookies` and :attr:`urlfetch.Response.cookiestring` to get response cookie dict and cookie string.

0.3.6 (2012-06-08)
+++++++++++++++++++

* simplify code
* Trace method without data and files, according to RFC2612
* ``urlencode(data, 1)`` so that ``urlencode({'param': [1,2,3]})`` => ``'param=1&param=2&param=3'``

0.3.5 (2012-04-24)
+++++++++++++++++++

* support specifying an IP for the request host, useful for testing API.

0.3.0 (2012-02-28)
+++++++++++++++++++

* python 3 compatible

0.2.2 (2012-02-22)
+++++++++++++++++++
* fix bug: file upload: file should always have a filename

0.2.1 (2012-02-22) 
+++++++++++++++++++

* more flexible file upload
* rename fetch2 to request
* add auth parameter, instead of put basic authentication info in url

0.1.2 (2011-12-07)
+++++++++++++++++++

* support basic auth

0.1 (2011-12-02)
+++++++++++++++++++

* first release
