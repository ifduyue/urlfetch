#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
urlfetch
~~~~~~~~~~

An easy to use HTTP client based on httplib.

:copyright: (c) 2011-2018 by Yue Du.
:license: BSD 2-clause License, see LICENSE for more details.
"""

__version__ = '1.1.0'
__author__ = 'Yue Du <ifduyue@gmail.com>'
__url__ = 'https://github.com/ifduyue/urlfetch'
__license__ = 'BSD 2-Clause License'

import os, sys, base64, codecs, uuid, stat, time, socket
from os.path import basename, dirname, abspath, join as pathjoin
from functools import partial
from io import BytesIO
import re
try:
    import simplejson as json
except ImportError:
    import json

py3k = sys.version_info >= (3, 0)
support_source_address = (sys.version_info >= (2, 7) and not py3k
                          or sys.version_info >= (3, 2))

if py3k:
    from http.client import HTTPConnection, HTTPSConnection
    from urllib.parse import urlencode
    import urllib.parse as urlparse
    import http.cookies as Cookie
    basestring = (str, bytes)
    unicode = str
    b = lambda s: s.encode('latin-1')
    u = lambda s: s
else:
    from httplib import HTTPConnection, HTTPSConnection
    from urllib import urlencode
    import urlparse
    import Cookie
    basestring = basestring
    unicode = unicode
    b = lambda s: s
    u = lambda s: unicode(s, 'unicode_escape')

__all__ = ('request', 'fetch', 'Session',
           'get', 'head', 'put', 'post', 'delete',
           'options', 'trace', 'patch',
           'UrlfetchException', 'ContentLimitExceeded', 'URLError',
           'ContentDecodingError', 'TooManyRedirects')


class UrlfetchException(IOError):
    "Base exception. All exceptions and errors will subclass from this."


class ContentLimitExceeded(UrlfetchException):
    "Content length is beyond the limit."


class URLError(UrlfetchException, ValueError):
    "Error parsing or handling the URL."


class ContentDecodingError(UrlfetchException):
    "Failed to decode the content."


class TooManyRedirects(UrlfetchException):
    """Too many redirects."""


class Timeout(UrlfetchException):
    """Request timed out."""


class cached_property(object):
    """Cached property.

    A property that is only computed once per instance and then replaces
    itself with an ordinary attribute. Deleting the attribute resets the
    property.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.__get = fget
        self.__set = fset
        self.__del = fdel
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__

    def __get__(self, instance, owner):
        if instance is None:
            # attribute is accessed through the owner class
            return self
        try:
            return instance.__dict__[self.__name__]
        except KeyError:
            value = instance.__dict__[self.__name__] = self.__get(instance)
            return value

    def __set__(self, instance, value):
        if instance is None:
            return self
        if self.__set is not None:
            value = self.__set(instance, value)
        instance.__dict__[self.__name__] = value

    def __delete__(self, instance):
        if instance is None:
            return self
        try:
            value = instance.__dict__.pop(self.__name__)
        except KeyError:
            pass
        else:
            if self.__del is not None:
                self.__del(instance, value)

    def setter(self, fset):
        return self.__class__(self.__get, fset, self.__del)

    def deleter(self, fdel):
        return self.__class__(self.__get, self.__set, fdel)


##############################################################################
# Core Methods and Classes ####################################################
##############################################################################

class Response(object):
    """A Response object.

    >>> import urlfetch
    >>> response = urlfetch.get("http://docs.python.org/")
    >>> response.total_time
    0.033042049407959
    >>> response.status, response.reason, response.version
    (200, 'OK', 10)
    >>> type(response.body), len(response.body)
    (<type 'str'>, 8719)
    >>> type(response.text), len(response.text)
    (<type 'unicode'>, 8719)
    >>> response.getheader('server')
    'Apache/2.2.16 (Debian)'
    >>> response.getheaders()
    [
        ('content-length', '8719'),
        ('x-cache', 'MISS from localhost'),
        ('accept-ranges', 'bytes'),
        ('vary', 'Accept-Encoding'),
        ('server', 'Apache/2.2.16 (Debian)'),
        ('last-modified', 'Tue, 26 Jun 2012 19:23:18 GMT'),
        ('connection', 'close'),
        ('etag', '"13cc5e4-220f-4c36507ded580"'),
        ('date', 'Wed, 27 Jun 2012 06:50:30 GMT'),
        ('content-type', 'text/html'),
        ('x-cache-lookup', 'MISS from localhost:8080')
    ]
    >>> response.headers
    {
        'content-length': '8719',
        'x-cache': 'MISS from localhost',
        'accept-ranges': 'bytes',
        'vary': 'Accept-Encoding',
        'server': 'Apache/2.2.16 (Debian)',
        'last-modified': 'Tue, 26 Jun 2012 19:23:18 GMT',
        'connection': 'close',
        'etag': '"13cc5e4-220f-4c36507ded580"',
        'date': 'Wed, 27 Jun 2012 06:50:30 GMT',
        'content-type': 'text/html',
        'x-cache-lookup': 'MISS from localhost:8080'
    }

    :raises: :class:`ContentLimitExceeded`
    """

    def __init__(self, r, **kwargs):

        for k in kwargs:
            setattr(self, k, kwargs[k])

        self._r = r  # httplib.HTTPResponse
        self.msg = r.msg

        #: Status code returned by server.
        self.status = r.status
        # compatible with requests
        #: An alias of :attr:`status`.
        self.status_code = r.status

        #: Reason phrase returned by server.
        self.reason = r.reason

        #: HTTP protocol version used by server.
        #: 10 for HTTP/1.0, 11 for HTTP/1.1.
        self.version = r.version

        #: total time
        self.total_time = kwargs.pop('total_time', None)

        self.getheader = r.getheader
        self.getheaders = r.getheaders

        self._content_encoding = self.getheader('content-encoding', None)
        self._decoder = None

        try:
            self.length_limit = int(kwargs.get('length_limit'))
        except:
            self.length_limit = None

        # if content (length) size is more than length_limit, skip
        content_length = int(self.getheader('Content-Length', 0))
        if self.length_limit and content_length > self.length_limit:
            self.close()
            raise ContentLimitExceeded("Content length is more than %d bytes"
                                       % self.length_limit)

    def read(self, chunk_size=8192):
        """Read content (for streaming and large files)

        :arg int chunk_size: size of chunk, default is 8192.
        """
        return self._r.read(chunk_size)

    def __iter__(self):
        return self

    def __next__(self):
        chunk = self.read()
        if not chunk:
            if self._decoder:
                chunk = self._decoder.flush()
                self._decoder = None
                return chunk
            else:
                raise StopIteration
        else:
            ce = self._content_encoding
            if ce in ('gzip', 'deflate'):
                if not self._decoder:
                    import zlib
                    if ce == 'gzip':
                        self._decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
                    else:
                        self._decoder = zlib.decompressobj()
                        try:
                            return self._decoder.decompress(chunk)
                        except zlib.error:
                            self._decoder = zlib.decompressobj(-zlib.MAX_WBITS)
                try:
                    return self._decoder.decompress(chunk)
                except (IOError, zlib.error) as e:
                    raise ContentDecodingError(e)

            if ce:
                raise ContentDecodingError('Unknown encoding: %s' % ce)
            return chunk

    next = __next__

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    @classmethod
    def from_httplib(cls, connection, **kwargs):
        """Make an :class:`~urlfetch.Response` object from a httplib response
        object."""
        return cls(connection, **kwargs)

    @cached_property
    def body(self):
        """Response body.

        :raises: :class:`ContentLimitExceeded`, :class:`ContentDecodingError`
        """
        content = b("")
        for chunk in self:
            content += chunk
            if self.length_limit and len(content) > self.length_limit:
                raise ContentLimitExceeded("Content length is more than %d "
                                           "bytes" % self.length_limit)

        return content

    # compatible with requests
    #: An alias of :attr:`body`.
    @property
    def content(self):
        return self.body

    @cached_property
    def text(self):
        """Response body in unicode."""
        return mb_code(self.content)

    @cached_property
    def json(self):
        """Load response body as json.

        :raises: :class:`ContentDecodingError`
        """
        try:
            return json.loads(self.text)
        except Exception as e:
            raise ContentDecodingError(e)

    @cached_property
    def headers(self):
        """Response headers.

        Response headers is a dict with all keys in lower case.

        >>> import urlfetch
        >>> response = urlfetch.get("http://docs.python.org/")
        >>> response.headers
        {
            'content-length': '8719',
            'x-cache': 'MISS from localhost',
            'accept-ranges': 'bytes',
            'vary': 'Accept-Encoding',
            'server': 'Apache/2.2.16 (Debian)',
            'last-modified': 'Tue, 26 Jun 2012 19:23:18 GMT',
            'connection': 'close',
            'etag': '"13cc5e4-220f-4c36507ded580"',
            'date': 'Wed, 27 Jun 2012 06:50:30 GMT',
            'content-type': 'text/html',
            'x-cache-lookup': 'MISS from localhost:8080'
        }
        """
        if py3k:
            return dict((k.lower(), v) for k, v in self.getheaders())
        else:
            return dict(self.getheaders())

    @cached_property
    def cookies(self):
        """Cookies in dict"""
        c = Cookie.SimpleCookie(self.getheader('set-cookie'))
        return dict((i.key, i.value) for i in c.values())

    @cached_property
    def cookiestring(self):
        """Cookie string"""
        return '; '.join('%s=%s' % (k, v) for k, v in self.cookies.items())

    @cached_property
    def links(self):
        """Links parsed from HTTP Link header"""
        ret = []
        linkheader = self.getheader('link')
        if not linkheader:
            return ret
        for i in linkheader.split(','):
            try:
                url, params = i.split(';', 1)
            except ValueError:
                url, params = i, ''
            link = {}
            link['url'] = url.strip('''<> '"''')
            for param in params.split(';'):
                try:
                    k, v = param.split('=')
                except ValueError:
                    break
                link[k.strip(''' '"''')] = v.strip(''' '"''')
            ret.append(link)
        return ret

    def close(self):
        """Close the connection."""
        self._r.close()

    def __del__(self):
        self.close()


class Session(object):
    """A session object.

    :class:`urlfetch.Session` can hold common headers and cookies.
    Every request issued by a :class:`urlfetch.Session` object will bring u
    these headers and cookies.

    :class:`urlfetch.Session` plays a role in handling cookies, just like a
    cookiejar.

    :arg dict headers: Init headers.
    :arg dict cookies: Init cookies.
    :arg tuple auth: (username, password) for basic authentication.
    """

    def __init__(self, headers={}, cookies={}, auth=None):
        """Init a :class:`~urlfetch.Session` object"""
        #: headers
        self.headers = headers.copy()
        #: cookies
        self.cookies = cookies.copy()

        if auth and isinstance(auth, (list, tuple)):
            auth = '%s:%s' % tuple(auth)
            auth = base64.b64encode(auth.encode('utf-8'))
            self.headers['Authorization'] = 'Basic ' + auth.decode('utf-8')

    def putheader(self, header, value):
        """Add an header to default headers."""
        self.headers[header] = value

    def popheader(self, header):
        """Remove an header from default headers."""
        return self.headers.pop(header)

    def putcookie(self, key, value=""):
        """Add an cookie to default cookies."""
        self.cookies[key] = value

    def popcookie(self, key):
        """Remove an cookie from default cookies."""
        return self.cookies.pop(key)

    @property
    def cookiestring(self):
        """Cookie string.

        It's assignalbe, and will change :attr:`~.Session.cookies`
        correspondingly.

        >>> s = Session()
        >>> s.cookiestring = 'foo=bar; 1=2'
        >>> s.cookies
        {'1': '2', 'foo': 'bar'}
        """
        return '; '.join('%s=%s' % (k, v) for k, v in self.cookies.items())

    @cookiestring.setter
    def cookiestring(self, value):
        """"Cookie string setter"""
        c = Cookie.SimpleCookie(value)
        sc = [(i.key, i.value) for i in c.values()]
        self.cookies = dict(sc)

    def snapshot(self):
        session = {
            'headers': self.headers.copy(),
            'cookies': self.cookies.copy()
        }
        return session

    def request(self, *args, **kwargs):
        """Issue a request."""
        headers = self.headers.copy()
        if self.cookiestring:
            headers['Cookie'] = self.cookiestring
        headers.update(kwargs.get('headers', {}))
        kwargs['headers'] = headers

        r = request(*args, **kwargs)
        self.cookies.update(r.cookies)

        return r

    def fetch(self, *args, **kwargs):
        """Fetch an URL"""
        data = kwargs.get('data', None)
        files = kwargs.get('files', {})

        if data and isinstance(data, (basestring, dict)) or files:
            return self.post(*args, **kwargs)
        return self.get(*args, **kwargs)

    def get(self, *args, **kwargs):
        """Issue a get request."""
        kwargs['method'] = 'GET'
        return self.request(*args, **kwargs)

    def post(self, *args, **kwargs):
        """Issue a post request."""
        kwargs['method'] = 'POST'
        return self.request(*args, **kwargs)

    def put(self, *args, **kwargs):
        """Issue a put request."""
        kwargs['method'] = 'PUT'
        return self.request(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Issue a delete request."""
        kwargs['method'] = 'DELETE'
        return self.request(*args, **kwargs)

    def head(self, *args, **kwargs):
        """Issue a head request."""
        kwargs['method'] = 'HEAD'
        return self.request(*args, **kwargs)

    def options(self, *args, **kwargs):
        """Issue a options request."""
        kwargs['method'] = 'OPTIONS'
        return self.request(*args, **kwargs)

    def trace(self, *args, **kwargs):
        """Issue a trace request."""
        kwargs['method'] = 'TRACE'
        return self.request(*args, **kwargs)

    def patch(self, *args, **kwargs):
        """Issue a patch request."""
        kwargs['method'] = 'PATCH'
        return self.request(*args, **kwargs)


def fetch(*args, **kwargs):
    """fetch an URL.

    :func:`~urlfetch.fetch` is a wrapper of :func:`~urlfetch.request`.
    It calls :func:`~urlfetch.get` by default. If one of parameter ``data``
    or parameter ``files`` is supplied, :func:`~urlfetch.post` is called.
    """
    data = kwargs.get('data', None)
    files = kwargs.get('files', {})

    if data and isinstance(data, (basestring, dict)) or files:
        return post(*args, **kwargs)
    return get(*args, **kwargs)

def match_no_proxy(host, no_proxy):
    ip_regex = r"(\d{1,3}).(\d{1,3}).(\d{1,3}).(\d{1,3})"
    no_proxy_ip_regex = r"(\d{1,3}).(\d{1,3}).(\d{1,3}).(\d{1,3})(?=/(\d+))?"
    ip_match = re.match(ip_regex, host)
    no_proxy_ip_match = re.match(no_proxy_ip_regex, no_proxy)
    if no_proxy_ip_match and ip_match:
        host_bits = "".join("{:08b}".format(int(section)) for section in ip_match.group(1, 2, 3, 4))
        no_proxy_bits = "".join("{:08b}".format(int(section)) for section in no_proxy_ip_match.group(1, 2, 3, 4))
        if no_proxy_ip_match.group(5) is not None:
            bit_match_count = int(no_proxy_ip_match.group(5))
            return host_bits[:bit_match_count] == no_proxy_bits[:bit_match_count]
        else:
            return host_bits == no_proxy_bits
    else:
        return host.endswith(no_proxy)

def request(url, method="GET", params=None, data=None, headers={},
            timeout=None, files={}, randua=False, auth=None, length_limit=None,
            proxies=None, trust_env=True, max_redirects=0,
            source_address=None, **kwargs):
    """request an URL

    :arg string url: URL to be fetched.
    :arg string method: (optional) HTTP method, one of ``GET``, ``DELETE``,
                        ``HEAD``, ``OPTIONS``, ``PUT``, ``POST``, ``TRACE``,
                        ``PATCH``. ``GET`` is the default.
    :arg dict/string params: (optional) Dict or string to attach to url as
                                querystring.
    :arg dict headers: (optional) HTTP request headers.
    :arg float timeout: (optional) Timeout in seconds
    :arg files: (optional) Files to be sended
    :arg randua: (optional) If ``True`` or ``path string``, use a random
                    user-agent in headers, instead of
                    ``'urlfetch/' + __version__``
    :arg tuple auth: (optional) (username, password) for basic authentication
    :arg int length_limit: (optional) If ``None``, no limits on content length,
                        if the limit reached raised exception 'Content length
                        is more than ...'
    :arg dict proxies: (optional) HTTP proxy, like {'http': '127.0.0.1:8888',
                                                 'https': '127.0.0.1:563'}
    :arg bool trust_env: (optional) If ``True``, urlfetch will get infomations
                        from env, such as HTTP_PROXY, HTTPS_PROXY
    :arg int max_redirects: (integer, optional) Max redirects allowed within a
                            request. Default is 0, which means redirects are
                            not allowed.
    :arg tuple source_address: (optional) A tuple of (host, port) to
                               specify the source_address to bind to. This
                               argument is ignored if you're using Python prior
                               to 2.7/3.2.
    :returns: A :class:`~urlfetch.Response` object
    :raises: :class:`URLError`, :class:`UrlfetchException`,
             :class:`TooManyRedirects`,
    """
    def make_connection(conn_type, host, port, timeout, source_address):
        """Return HTTP or HTTPS connection."""
        if support_source_address:
            kwargs = {'timeout': timeout, 'source_address': source_address}
        else:
            kwargs = {'timeout': timeout}
            if source_address is not None:
                raise UrlfetchException('source_address requires'
                                        'Python 2.7/3.2 or newer versions')
        if conn_type == 'http':
            conn = HTTPConnection(host, port, **kwargs)
        elif conn_type == 'https':
            conn = HTTPSConnection(host, port, **kwargs)
        else:
            raise URLError('Unknown Connection Type: %s' % conn_type)
        return conn

    via_proxy = False

    method = method.upper()
    if method not in ALLOWED_METHODS:
        raise UrlfetchException("Method should be one of " +
                                ", ".join(ALLOWED_METHODS))
    if params:
        if isinstance(params, dict):
            url = url_concat(url, params)
        elif isinstance(params, basestring):
            if url[-1] not in ('?', '&'):
                url += '&' if ('?' in url) else '?'
            url += params

    parsed_url = parse_url(url)

    reqheaders = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, compress, identity, *',
        'User-Agent': random_useragent(randua),
        'Host': parsed_url['http_host']
    }

    # Proxy support
    scheme = parsed_url['scheme']
    if proxies is None and trust_env:
        proxies = PROXIES

    ignore_hosts = PROXY_IGNORE_HOSTS
    if trust_env:
        no_proxy = os.getenv('no_proxy') or os.getenv('NO_PROXY')
        if no_proxy:
            ignore_hosts = no_proxy.split(",")

    proxy = proxies.get(scheme)
    if proxy and not any(match_no_proxy(parsed_url['host'], host) for host in ignore_hosts):
        via_proxy = True
        if '://' not in proxy:
            proxy = '%s://%s' % (scheme, proxy)
        parsed_proxy = parse_url(proxy)
        # Proxy-Authorization
        if parsed_proxy['username'] and parsed_proxy['password']:
            proxyauth = '%s:%s' % (parsed_proxy['username'],
                                   parsed_proxy['password'])
            proxyauth = base64.b64encode(proxyauth.encode('utf-8'))
            reqheaders['Proxy-Authorization'] = 'Basic ' + \
                                                proxyauth.decode('utf-8')
        conn = make_connection(scheme, parsed_proxy['host'],
                               parsed_proxy['port'], timeout, source_address)
    else:
        conn = make_connection(scheme, parsed_url['host'], parsed_url['port'],
                               timeout, source_address)

    if not auth and parsed_url['username'] and parsed_url['password']:
        auth = (parsed_url['username'], parsed_url['password'])
    if auth:
        if isinstance(auth, (list, tuple)):
            auth = '%s:%s' % tuple(auth)
        auth = base64.b64encode(auth.encode('utf-8'))
        reqheaders['Authorization'] = 'Basic ' + auth.decode('utf-8')

    if files:
        content_type, data = encode_multipart(data, files)
        reqheaders['Content-Type'] = content_type
    elif isinstance(data, dict):
        data = urlencode(data, 1)

    if isinstance(data, basestring) and not files:
        # httplib will set 'Content-Length', also you can set it by yourself
        reqheaders["Content-Type"] = "application/x-www-form-urlencoded"
        # what if the method is GET, HEAD or DELETE
        # just do not make so much decisions for users

    reqheaders.update(headers)

    start_time = time.time()
    try:
        request_url = url if via_proxy else parsed_url['uri']
        conn.request(method, request_url, data, reqheaders)
        resp = conn.getresponse()
    except socket.timeout as e:
        raise Timeout(e)
    except Exception as e:
        raise UrlfetchException(e)

    end_time = time.time()
    total_time = end_time - start_time
    history = []
    response = Response.from_httplib(resp, reqheaders=reqheaders,
                                     length_limit=length_limit,
                                     history=history[:], url=url,
                                     total_time=total_time,
                                     start_time=start_time)

    while (response.status in (301, 302, 303, 307) and
           'location' in response.headers and max_redirects):
        response.body, response.close(), history.append(response)

        if len(history) > max_redirects:
            raise TooManyRedirects('max_redirects exceeded')

        method = method if response.status == 307 else 'GET'
        location = response.headers['location']
        if location[:2] == '//':
            url = parsed_url['scheme'] + ':' + location
        else:
            url = urlparse.urljoin(url, location)
        parsed_url = parse_url(url)

        reqheaders['Host'] = parsed_url['http_host']
        reqheaders['Referer'] = response.url

        # Proxy
        scheme = parsed_url['scheme']
        proxy = proxies.get(scheme)
        if proxy and parsed_url['host'] not in PROXY_IGNORE_HOSTS:
            via_proxy = True
            if '://' not in proxy:
                proxy = '%s://%s' % (parsed_url['scheme'], proxy)
            parsed_proxy = parse_url(proxy)
            # Proxy-Authorization
            if parsed_proxy['username'] and parsed_proxy['password']:
                proxyauth = '%s:%s' % (parsed_proxy['username'],
                                       parsed_proxy['username'])
                proxyauth = base64.b64encode(proxyauth.encode('utf-8'))
                reqheaders['Proxy-Authorization'] = 'Basic ' + \
                                                    proxyauth.decode('utf-8')
            conn = make_connection(scheme, parsed_proxy['host'],
                                   parsed_proxy['port'], timeout,
                                   source_address)
        else:
            via_proxy = False
            reqheaders.pop('Proxy-Authorization', None)
            conn = make_connection(scheme, parsed_url['host'],
                                   parsed_url['port'], timeout, source_address)

        try:
            request_url = url if via_proxy else parsed_url['uri']
            conn.request(method, request_url, data, reqheaders)
            resp = conn.getresponse()
        except socket.timeout as e:
            raise Timeout(e)
        except Exception as e:
            raise UrlfetchException(e)

        response = Response.from_httplib(resp, reqheaders=reqheaders,
                                         length_limit=length_limit,
                                         history=history[:], url=url,
                                         total_time=total_time,
                                         start_time=start_time)

    return response


##############################################################################
# Shortcuts and Helpers #######################################################
##############################################################################

def _partial_method(method):
    func = partial(request, method=method)
    func.__doc__ = 'Issue a %s request' % method.lower()
    func.__name__ = method.lower()
    func.__module__ = request.__module__
    return func

get = _partial_method("GET")
post = _partial_method("POST")
put = _partial_method("PUT")
delete = _partial_method("DELETE")
head = _partial_method("HEAD")
options = _partial_method("OPTIONS")
trace = _partial_method("TRACE")
patch = _partial_method("PATCH")

del _partial_method


class ObjectDict(dict):
    """Makes a dictionary behave like an object."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


def parse_url(url):
    """Return a dictionary of parsed url

    Including scheme, netloc, path, params, query, fragment, uri, username,
    password, host, port and http_host
    """
    try:
        url = unicode(url)
    except UnicodeDecodeError:
        pass

    if py3k:
        make_utf8 = lambda x: x
    else:
        make_utf8 = lambda x: isinstance(x, unicode) and x.encode('utf-8') or x

    if '://' in url:
        scheme, url = url.split('://', 1)
    else:
        scheme = 'http'
    url = 'http://' + url
    parsed = urlparse.urlsplit(url)
    r = ObjectDict()
    r['scheme'] = make_utf8(scheme)
    r['netloc'] = make_utf8(parsed.netloc)
    r['path'] = make_utf8(parsed.path)
    r['query'] = make_utf8(parsed.query)
    r['fragment'] = make_utf8(parsed.fragment)
    r['uri'] = make_utf8(parsed.path)
    if parsed.query:
        r['uri'] += '?' + make_utf8(parsed.query)
    r['username'] = make_utf8(parsed.username)
    r['password'] = make_utf8(parsed.password)
    host = make_utf8(parsed.hostname.encode('idna').decode('utf-8'))
    r['host'] = r['hostname'] = host
    try:
        r['port'] = parsed.port
    except ValueError:
        r['port'] = None
    if r['port']:
        r['http_host'] = '%s:%d' % (r['host'], r['port'])
    else:
        r['http_host'] = r['host']

    return r


def get_proxies_from_environ():
    """Get proxies from os.environ."""
    proxies = {}
    http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
    https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
    if http_proxy:
        proxies['http'] = http_proxy
    if https_proxy:
        proxies['https'] = https_proxy
    return proxies


def mb_code(s, coding=None, errors='replace'):
    """encoding/decoding helper."""
    if isinstance(s, unicode):
        return s if coding is None else s.encode(coding, errors=errors)
    for c in ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5'):
        try:
            s = s.decode(c)
            return s if coding is None else s.encode(coding, errors=errors)
        except:
            pass
    return unicode(s, errors=errors)


def random_useragent(filename=True):
    """Returns a User-Agent string randomly from file.

    :arg string filename: (Optional) Path to the file from which a random
        useragent is generated. By default it's ``True``, a file shipped
        with this module will be used.
    :returns: An user-agent string.
    """
    import random

    default_ua = 'urlfetch/%s' % __version__

    if isinstance(filename, basestring):
        filenames = [filename]
    else:
        filenames = []

    if filename and UAFILE:
        filenames.append(UAFILE)

    for filename in filenames:
        try:
            st = os.stat(filename)
            if stat.S_ISREG(st.st_mode) and os.access(filename, os.R_OK):
                break
        except:
            pass
    else:
        return default_ua

    with open(filename, 'rb') as f:
        filesize = st.st_size
        pos = 0
        r = random.Random()

        # try getting a valid line for no more than 3 times
        for i in range(3):

            pos += r.randint(0, filesize)
            pos %= filesize
            f.seek(pos)

            # in case we are in middle of a line
            f.readline()

            line = f.readline()
            if not line:
                if f.tell() == filesize:
                    # end of file
                    f.seek(0)
                    line = f.readline()

            line = line.strip()
            if line and line[0] != '#':
                return line

    return default_ua


def url_concat(url, args, keep_existing=True):
    """Concatenate url and argument dictionary

    >>> url_concat("http://example.com/foo?a=b", dict(c="d"))
    'http://example.com/foo?a=b&c=d'

    :arg string url: URL being concat to.
    :arg dict args: Args being concat.
    :arg bool keep_existing: (Optional) Whether to keep the args which are
                            alreay in url, default is ``True``.
    """
    if not args:
        return url

    if keep_existing:
        if url[-1] not in ('?', '&'):
            url += '&' if ('?' in url) else '?'
        return url + urlencode(args, 1)
    else:
        url, seq, query = url.partition('?')
        query = urlparse.parse_qs(query, True)
        query.update(args)
        return url + '?' + urlencode(query, 1)


def choose_boundary():
    """Generate a multipart boundry.

    :returns: A boundary string
    """
    global BOUNDARY_PREFIX
    if BOUNDARY_PREFIX is None:
        BOUNDARY_PREFIX = "urlfetch"
        try:
            uid = repr(os.getuid())
            BOUNDARY_PREFIX += "." + uid
        except AttributeError:
            pass
        try:
            pid = repr(os.getpid())
            BOUNDARY_PREFIX += "." + pid
        except AttributeError:
            pass

    return "%s.%s" % (BOUNDARY_PREFIX, uuid.uuid4().hex)


def encode_multipart(data, files):
    """Encode multipart.

    :arg dict data: Data to be encoded
    :arg dict files: Files to be encoded
    :returns: Encoded binary string
    :raises: :class:`UrlfetchException`
    """
    body = BytesIO()
    boundary = choose_boundary()
    part_boundary = b('--%s\r\n' % boundary)
    writer = codecs.lookup('utf-8')[3]

    if isinstance(data, dict):
        for name, values in data.items():
            if not isinstance(values, (list, tuple, set)):
                # behave like urllib.urlencode(dict, 1)
                values = (values, )
            for value in values:
                body.write(part_boundary)
                writer(body).write('Content-Disposition: form-data; '
                                   'name="%s"\r\n' % name)
                body.write(b'Content-Type: text/plain\r\n\r\n')
                if isinstance(value, int):
                    value = str(value)
                if py3k and isinstance(value, str):
                    writer(body).write(value)
                else:
                    body.write(value)
                body.write(b'\r\n')

    for fieldname, f in files.items():
        if isinstance(f, tuple):
            filename, f = f
        elif hasattr(f, 'name'):
            filename = basename(f.name)
        else:
            filename = None
            raise UrlfetchException("file must has filename")

        if hasattr(f, 'read'):
            value = f.read()
        elif isinstance(f, basestring):
            value = f
        else:
            value = str(f)

        body.write(part_boundary)
        if filename:
            writer(body).write('Content-Disposition: form-data; name="%s"; '
                               'filename="%s"\r\n' % (fieldname, filename))
            body.write(b'Content-Type: application/octet-stream\r\n\r\n')
        else:
            writer(body).write('Content-Disposition: form-data; name="%s"'
                               '\r\n' % name)
            body.write(b'Content-Type: text/plain\r\n\r\n')

        if py3k and isinstance(value, str):
            writer(body).write(value)
        else:
            body.write(value)
        body.write(b'\r\n')

    body.write(b('--' + boundary + '--\r\n'))

    content_type = 'multipart/form-data; boundary=%s' % boundary

    return content_type, body.getvalue()

##############################################################################
# Constants and Globals #######################################################
##############################################################################

ALLOWED_METHODS = ("GET", "DELETE", "HEAD", "OPTIONS", "PUT", "POST", "TRACE",
                   "PATCH")
PROXY_IGNORE_HOSTS = ('127.0.0.1', 'localhost')
PROXIES = get_proxies_from_environ()
BOUNDARY_PREFIX = None

UAFILENAME = 'urlfetch.useragents.list'
UAFILE = next((i for i in set((pathjoin(sys.prefix, UAFILENAME),
                               pathjoin(sys.prefix, 'local', UAFILENAME),
                               pathjoin(dirname(abspath(__file__)), UAFILENAME)))
                if os.path.isfile(i)), None)
