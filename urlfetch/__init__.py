#coding: utf8

'''
urlfetch 
~~~~~~~~~~

An easy to use HTTP client based on httplib.

:copyright: (c) 2011-2012  Elyes Du.
:license: BSD 2-clause License, see LICENSE for details.
'''

#   TODO: sometimes encoding format coming from server in wrong format, make mapping known errors
#   TODO: add limitation of max content length to avoid memory leaks
#   TODO: handling exceptions for h.request/h.response
#   TODO: add support of chunked transfer encoding http://en.wikipedia.org/wiki/Chunked_transfer_encoding

__version__ = '0.3.6'
__author__ = 'Elyes Du <lyxint@gmail.com>'
__url__ = 'https://github.com/lyxint/urlfetch'

from . import util
from . import uas

if util.py3k:
    from http.client import HTTPConnection, HTTPSConnection, HTTPException
    from http.client import HTTP_PORT, HTTPS_PORT
    from urllib.parse import urlencode, quote as urlquote, quote_plus as urlquote_plus
    import urllib.parse as urlparse
    import http.cookies as Cookie
    basestring = (str, bytes)
    def b(s):
        return s.encode('latin-1')
    def u(s):
        return s
else:
    from httplib import HTTPConnection, HTTPSConnection, HTTPException
    from httplib import HTTP_PORT, HTTPS_PORT
    from urllib import urlencode, quote as urlquote, quote_plus as urlquote_plus
    import urlparse
    import Cookie
    def b(s):
        return s
    def u(s):
        return unicode(s, "unicode_escape")

import socket
import base64
from functools import partial
import os
from io import BytesIO
import codecs
writer = codecs.lookup('utf-8')[3]


__all__ = [
    'sc2cs', 'fetch', 'request', 
    'get', 'head', 'put', 'post', 'delete', 'options',
    'Headers', 'UrlfetchException',
] 

_allowed_methods = ("GET", "DELETE", "HEAD", "OPTIONS", "PUT", "POST", "TRACE", "PATCH")

class UrlfetchException(Exception): pass

def sc2cs(sc):
    '''Convert Set-Cookie header to cookie string.
    
    Set-Cookie can be retrieved from a :class:`~urlfetch.Response` instance::
    
        sc = response.getheader('Set-Cookie')
    
    :param sc: Set-Cookie
    :type sc: string
    :rtype: cookie string, which is name=value pairs joined by ``\;``.
    '''
    c = Cookie.SimpleCookie(sc)
    sc = ['%s=%s' % (i.key, i.value) for i in c.itervalues()]
    return '; '.join(sc)


_boundary_prefix = None
def choose_boundary():
    '''Generate a multipart boundry.
    
    :rtype: string
    '''
    
    global _boundary_prefix
    if _boundary_prefix is None:
        _boundary_prefix = "urlfetch"
        import os
        try:
            uid = repr(os.getuid())
            _boundary_prefix += "." + uid
        except AttributeError: pass
        try:
            pid = repr(os.getpid())
            _boundary_prefix += "." + pid
        except AttributeError: pass
    import uuid
    return "(*^__^*)%s.%s" % (_boundary_prefix, uuid.uuid4().hex)

def _encode_multipart(data, files):
    '''Encode multipart.
    
    :param data: data to be encoded
    :type data: dict
    :param files: files to be encoded
    :type files: dict
    :rtype: encoded binary string
    '''
    
    body = BytesIO()
    boundary = choose_boundary()
    part_boundary = b('--%s\r\n' % boundary)

    if isinstance(data, dict):
        for name, value in data.items():
            body.write(part_boundary)
            writer(body).write('Content-Disposition: form-data; name="%s"\r\n' % name)
            body.write(b'Content-Type: text/plain\r\n\r\n')
            if util.py3k and isinstance(value, str): 
                writer(body).write(value)
            else:
                body.write(value)
            body.write(b'\r\n')
            

    for fieldname, f in files.items():
        if isinstance(f, tuple):
            filename, f = f
        elif hasattr(f, 'name'):
            filename = os.path.basename(f.name)
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
            writer(body).write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (fieldname, filename))
            body.write(b'Content-Type: application/octet-stream\r\n\r\n')
        else:
            writer(body).write('Content-Disposition: form-data; name="%s"\r\n' % name)
            body.write(b'Content-Type: text/plain\r\n\r\n')

        if util.py3k and isinstance(value, str):
            writer(body).write(value)
        else:
            body.write(value)
        body.write(b'\r\n')

    body.write(b('--' + boundary + '--\r\n'))

    content_type = 'multipart/form-data; boundary=%s' % boundary
    #body.write(b(content_type))

    return content_type, body.getvalue()

class Headers(object):
    ''' Headers
    
    to simplify fetch() interface, class Headers helps to manipulate parameters
    '''
    def __init__(self):
        ''' make default headers '''
        self.__headers = {
            'Accept': '*/*',
            'User-Agent':  'urlfetch/' + __version__,
        }
    
    def random_user_agent(self):
        ''' generate random User-Agent string from uas.py collection '''
        self.__headers['User-Agent'] = uas.randua()
    
    def basic_auth(self, username, password):
        ''' add username/password for basic authentication '''
        auth = '%s:%s' % (username, password)
        auth = base64.b64encode(auth.encode('utf-8'))
        self.__headers['Authorization'] = 'Basic ' + auth.decode('utf-8')
    
    def items(self):
        ''' return headers dictionary '''
        return self.__headers

class Response(object):
    '''A Response object.
    
    ::
        
        >>> import urlfetch
        >>> response = urlfetch.get("http://docs.python.org/")
        >>> 
        >>> response.status, response.reason, response.version
        (200, 'OK', 10)
        >>> type(response.body), len(response.text)
        (<type 'str'>, 8719)
        >>> type(response.text), len(response.text)
        (<type 'unicode'>, 8719
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

    '''
    
    def __init__(self, r, **kwargs):
        self._r = r # httplib.HTTPResponse
        self.msg = r.msg
        
        #: Status code returned by server.
        self.status = r.status
        
        #: Reason phrase returned by server.
        self.reason = r.reason
        
        #: HTTP protocol version used by server. 10 for HTTP/1.0, 11 for HTTP/1.1.
        self.version = r.version
        self._body = None
        self._headers = None
        self._text = None

        self.getheader = r.getheader
        self.getheaders = r.getheaders

        for k in kwargs:
            setattr(self, k, kwargs[k])
    
        if kwargs.get('prefetch', False):
            self._body = self._r.read()
            self.close()
        
    @classmethod
    def from_httplib(cls, r, **kwargs):
        '''Generate a :class:`~urlfetch.Response` object from an httplib response object.'''
        
        return cls(r, **kwargs)
        
    @property
    def body(self):
        '''Response body.'''
        
        if self._body is None:
            self._body = self._r.read()
        return self._body
    
    @property
    def text(self):
        '''Response body in unicode.'''
        
        if self._text is None:
            self._text = util.mb_code(self.body)
        return self._text
    
    @property
    def headers(self):
        '''Response headers.
        
        Response headers is a dict with all keys in lower case.
        
        ::
        
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
        
        '''
        
        if self._headers is None:
            self._headers = dict((k.lower(), v) for k, v in self._r.getheaders())
        return self._headers

    def close(self):
        if hasattr(self, 'connection'):
            self.connection.close()
        self._r.close()

    def __del__(self):
        self.close()
        

def fetch(url, data=None, headers={}, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, files={}, prefetch=True):
    ''' fetch an URL.
    
    :param url: URL to be fetched.
    :type url: string
    :param headers: HTTP request headers
    :type headers: dict, optional
    :param timeout: timeout in seconds, socket._GLOBAL_DEFAULT_TIMEOUT by default
    :type timeout: integer or float, optional
    :param files: files to be sended
    :type files: dict, optional
    :param prefetch: if ``True``, reponse body will be read in automatically, else reponse body will be read in the first you access :meth:`urlfetch.Response.body`
    :type prefetch: bool, optional, default is ``True``
    :rtype: A :class:`~urlfetch.Response` object
    
    :func:`~urlfetch.fetch` is a wrapper of :func:`~urlfetch.request`.
    It calls :func:`~urlfetch.get` by default. If one of parameter ``data``
    or parameter ``files`` is supplied, :func:`~urlfetch.post` is called.
    '''
    
    local = locals()
    if data is not None and isinstance(data, (basestring, dict)):
        return post(**local)
    return get(**local)


def request(url, method="GET", data=None, headers={}, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
            files={}, prefetch=True):
            
    ''' request an URL
    
    :param url: URL to be fetched.
    :type url: string
    :param method: HTTP method, one of ``GET``, ``DELETE``, ``HEAD``, ``OPTIONS``, ``PUT``, ``POST``, ``TRACE``, ``PATCH``. ``GET`` by default.
    :type method: string, optional
    :param headers: HTTP request headers
    :type headers: dict, optional
    :param timeout: timeout in seconds, socket._GLOBAL_DEFAULT_TIMEOUT by default
    :type timeout: integer or float, optional
    :param files: files to be sended
    :type files: dict, optional
    :param prefetch: if ``True``, reponse body will be read in automatically, else reponse body will be read in the first you access :class:`~urlfetch.Response`.body
    :type prefetch: bool, optional, default is ``True``
    :rtype: A :class:`~urlfetch.Response` object
    '''

    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    method = method.upper()
    if method not in _allowed_methods:
        raise UrlfetchException("Method shoud be one of " + ", ".join(_allowed_methods))

    requrl = path
    if query: requrl += '?' + query
    # do not add fragment
    #if fragment: requrl += '#' + fragment
    
    # handle 'Host'
    if ':' in netloc:
        host, port = netloc.rsplit(':', 1)
        port = int(port)
    else:
        host, port = netloc, None
    host = host.encode('idna').decode('utf-8')
    
    if scheme == 'https':
        h = HTTPSConnection(host, port=port, timeout=timeout)
    elif scheme == 'http':
        h = HTTPConnection(host, port=port, timeout=timeout)
    else:
        raise UrlfetchException('Unsupported protocol %s' % scheme)
        
    # default request headers
    reqheaders = Headers().items()
    
    if files:
        content_type, data = _encode_multipart(data, files)
        reqheaders['Content-Type'] = content_type
    elif isinstance(data, dict):
        data = urlencode(data, 1)
    
    if isinstance(data, basestring) and not files:
        # httplib will set 'Content-Length', also you can set it by yourself
        reqheaders["Content-Type"] = "application/x-www-form-urlencoded"
        # what if the method is GET, HEAD or DELETE 
        # just do not make so much decisions for users

    for k, v in headers.items():
        reqheaders[k.title()] = v 
    
    h.request(method, requrl, data, reqheaders)
    response = h.getresponse()
    return Response.from_httplib(response, prefetch=prefetch, reqheaders=reqheaders, connection=h)

# some shortcuts
get = partial(request, method="GET")
post = partial(request, method="POST")
put = partial(request, method="PUT")
delete = partial(request, method="DELETE")
head = partial(request, method="HEAD")
options = partial(request, method="OPTIONS")
# No entity body can be sent with a TRACE request. 
trace = partial(request, method="TRACE", files={}, data=None)
patch = partial(request, method="PATCH")

