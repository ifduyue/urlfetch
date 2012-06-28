#coding: utf8

'''
urlfetch 
~~~~~~~~~~

An easy to use HTTP client based on httplib.

:copyright: (c) 2011-2012  Elyes Du.
:license: BSD 2-clause License, see LICENSE for details.
'''

__version__ = '0.3.6'
__author__ = 'Elyes Du <lyxint@gmail.com>'
__url__ = 'https://github.com/lyxint/urlfetch'

import os, sys

if sys.version_info >= (3, 0):
    py3k = True
    unicode = str
else:
    py3k = False

if py3k:
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
            if py3k and isinstance(value, str): 
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

        if py3k and isinstance(value, str):
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

    def put(self, k, v):
        ''' add new parameter to headers '''
        self.__headers[k.title()] = v
    
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
        >>> type(response.body), len(response.body)
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
    

        # length_limit: if content (length) size is more than length_limit -> skip
        try:
            self.length_limit = int(kwargs.get('length_limit'))
        except:
            self.length_limit = None
            
        if self.length_limit and int(self.getheader('Content-Length', 0)) > self.length_limit:
            self.close()
            raise UrlfetchException("Content length is more than %d bytes" % length_limit)  

        
        self._body = self._download_content()
        self.close()


    def _download_content(self, chunk_size = 10 * 1024):
        ''' download content if chunked
        
        chunk_size: size of chunk, default: 10 * 1024
        '''
        content = b("")
        while True:
            chunk = self._r.read(chunk_size)

            if not chunk:
                break

            content += chunk

            if self.length_limit and len(content) > self.length_limit:
                raise UrlfetchException("Content length is more than %d bytes" % length_limit)  

        return content
        
    @classmethod
    def from_httplib(cls, r, **kwargs):
        '''Generate a :class:`~urlfetch.Response` object from an httplib response object.'''
        
        return cls(r, **kwargs)
        
    @property
    def body(self):
        '''Response body.'''
        
        if self._body is None:
            self._body = self._download_content()
        return self._body
    
    @property
    def text(self):
        '''Response body in unicode.'''
        
        if self._text is None:
            self._text = mb_code(self.body)
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
        

def fetch(url, data=None, headers={}, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, 
        files={}, length_limit=None, **kwargs):
    ''' fetch an URL.
    
    :param url: URL to be fetched.
    :type url: string
    :param headers: HTTP request headers
    :type headers: dict, optional
    :param timeout: timeout in seconds, socket._GLOBAL_DEFAULT_TIMEOUT by default
    :type timeout: integer or float, optional
    :param files: files to be sended
    :type files: dict, optional
    :param length_limit: if ``None``, no limits on content length, if the limit reached raised exception 'Content length is more than ...'
    :type length_limit: integer or None, default is ``none``
    :rtype: A :class:`~urlfetch.Response` object
    
    :func:`~urlfetch.fetch` is a wrapper of :func:`~urlfetch.request`.
    It calls :func:`~urlfetch.get` by default. If one of parameter ``data``
    or parameter ``files`` is supplied, :func:`~urlfetch.post` is called.
    '''
    
    local = locals()
    local.pop('kwargs')
    local.update(kwargs)

    if data is not None and isinstance(data, (basestring, dict)):
        return post(**local)
    return get(**local)


def request(url, method="GET", data=None, headers={}, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
            files={}, length_limit=None, **kwargs):
            
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
    :param length_limit: if ``None``, no limits on content length, if the limit reached raised exception 'Content length is more than ...'
    :type length_limit: integer or None, default is ``none``
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
    return Response.from_httplib(response, reqheaders=reqheaders, connection=h, length_limit=length_limit)

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

#uas come from http://www.vwp-online.de/ua.php?ua_type=browser
# without mobile device user-agents
_uas = (
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.5) Gecko/20031007 Firebird/0.7''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.0.1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; nl; rv:1.8.0.1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.12)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.2)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.6)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.10)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.0; zh-TW; rv:1.8.0.1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; sl; rv:1.8.0.1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.0.1)''',
    '''Mozilla/5.0 (X11; Linux i686; rv:1.7.5)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:1.7.2)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.7.6)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8a3)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.8.0.1)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.4)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.7.12)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.7.8)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.6)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; el; rv:1.8.0.1)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.7)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.5)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; MathPlayer 2.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; Alexa Toolbar)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; FDM)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.1) Gecko/20061205 Iceweasel/2.0.0.1 (Debian-2.0.0.1+dfsg-2)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.6) Gecko/20060808''',
    '''Mozilla/4.0 (compatible; Mozilla/5.0; Windows NT 5.0; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; FDM; .NET CLR 2.0.50727)''',
    '''Opera/9.10 (Windows NT 5.1; U; en)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Win64; x64; .NET CLR 2.0.50727; SLCC1; Media Center PC 5.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.1) Gecko/20040707''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; WFX; .NET CLR 1.0.3705)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; iOpus-I-M)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9a6pre) Gecko/20070702 Minefield/3.0a6pre''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9a7pre) Gecko/2007070604 Minefield/3.0a7pre''',
    '''Mozilla/5.0 (compatible; idiot; ka)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en) AppleWebKit/522.11 (KHTML, like Gecko) Version/3.0.2 Safari/522.12''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 1.0.3705)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9a1) Gecko/20061204 GranParadiso/3.0a1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.8.1.2) Gecko/20070224 BonEcho/2.0.0.2 (tete009 SSE PGO)''',
    '''Mozilla/6.0 (compatible; MSIE 8.0; Windows 7)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1a3) Gecko/20060526 BonEcho/2.0a3''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Arcor 5.003; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.4) Gecko/20070508 Iceweasel/2.0.0.4 (Debian-2.0.0.4-0etch1)''',
    '''Mozilla/4.8 [en] (Windows NT 6.0; U)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506; MSN Optimized;DE; MSN Optimized;DE)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; uk; rv:1.8.1.2) Gecko/20070222 SeaMonkey/1.1.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9a8pre) Gecko/2007090104 Minefield/3.0a8pre''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.590; .NET CLR 3.5.20706)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 1.1.4322; .NET CLR 3.0.04506.30)''',
    '''Opera/9.50 (Windows NT 6.0; U; en)''',
    '''Mozilla/5.0 (X11; U; Linux; rv:1.8.0.10) Gecko/20070510''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR={DB86ECE3-D9F3-4dd8-B43E-3F5048C821D0}; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2; WOW64)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; DownloadSpeed; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en) AppleWebKit/419.3 (KHTML, like Gecko) Safari/419.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.8pre) Gecko/20071020 BonEcho/2.0.0.8pre''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X; nl-nl) AppleWebKit/419.3 (KHTML, like Gecko) Safari/419.3''',
    '''Mozilla/4.0 (compatible; MSIE 7.0;Windows NT 5.1;.NET CLR 1.1.4322;.NET CLR 2.0.50727;.NET CLR 3.0.04506.30)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.8.1.9) Gecko/20071030 SeaMonkey/1.1.6''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727) Sleipnir/2.6.0''',
    '''Mozilla/4.0+(compatible;+MSIE+6.0;+Windows+NT+5.1;+SV1;+.NET+CLR+1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727) Sleipnir/2.6.0''',
    '''Mozilla/5.0 (X11; U; SunOS sun4m; en-US; rv:1.4b) Gecko/20030517 Mozilla Firebird/0.6''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)''',
    '''Mozilla/7.0 (not compatible; MSIE 4.2; Linux LE 0.016; libwww-FM/2.14)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FDM; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b2pre) Gecko/2007110905 Minefield/3.0b2pre X.a1e''',
    '''Mozilla/5.0 (Windows; U; Windows XP) Gecko MultiZilla/1.6.1.0a''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.8.1.11) Gecko/20071223 SeaMonkey/1.1.7''',
    '''Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; TOB 6.05; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506; FDM)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.6) Gecko/20070723 Iceweasel/2.0.0.6 (Debian-2.0.0.6-0etch1+lenny1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.2) Gecko/20040804 Netscape/7.2 (ax)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; U; en)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50215; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0 x64; en-US; rv:1.8.1.11) Gecko/20071203 BonEcho/2.0.0.11 (mmoy CE K8C-X04)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648)''',
    '''Mozilla/4.0 (MSIE 7.0; Windows NT 6.0)''',
    '''Mozilla/5.0 (X11; ; Linux i686; rv:1.8.1.11) Gecko/20071201''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.0; Windows NT 5.1; .NET CLR 1.1.4322)''',
    '''Opera/9.50 (X11; Linux i686; U; en)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-us) AppleWebKit/523.10.6 (KHTML, like Gecko) Version/3.0.4 Safari/523.10.6''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.2pre) Gecko/20070111 SeaMonkey/1.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; FDM; .NET CLR 3.0.04506.648)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506; Media Center PC 5.0)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b4pre) Gecko/2008021204 Minefield/3.0b4pre''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; Alexa Toolbar; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Danger hiptop 2.0; U; AvantGo 3.2)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; MSN Optimized;XL; MSN Optimized;XL)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9a1) Gecko/20070308 Minefield/3.0a1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.12) Gecko/20080129 Iceape/1.1.8 (Debian-1.1.8-2)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 1.0.3705; Media Center PC 3.1; .NET CLR 2.0.50727; Media Center PC 2.8)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 4.01; Windows 3.11)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.12) Gecko/20080213 BonEcho/2.0.0.12''',
    '''Mozilla/4.0 (PSP (PlayStation Portable); 2.00)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b5pre) Gecko/2008032005 Minefield/3.0b5pre''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b4) Gecko/2008030714 Firefox/3.0b4''',
    '''Opera/9.50 (Windows NT 5.1; U; en)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Zango 10.0.341.0)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-GB; rv:1.9b4) Gecko/2008030317 Firefox/3.0b4''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; FDM)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; WOW64; .NET CLR 1.1.4322; Alexa Toolbar)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9pre) Gecko/2008042006 Minefield/3.0pre''',
    '''Mozilla/5.0 (en-US)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.14eol) Gecko/20070505 (Debian-1.8.0.15~pre080323b-0etch1) Epiphany/2.14''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; WOW64; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Opera/8.51 (X11; Linux i686; U; en)''',
    '''Mozilla/5.0 (X11; U; Linux i586; en-US; rv:1.7.3) Gecko/20040924 Epiphany/1.4.4 (Ubuntu)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; MRA 5.0 (build 02094); .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; T-Online IE7; T-Online IE7)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.14) Gecko/20080417 BonEcho/2.0.0.14''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b5) Gecko/2008050509 Firefox/3.0b5''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.14) Gecko/20080404 Iceweasel/2.0.0.14 (Debian-2.0.0.14-0etch1)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.8) Gecko/20050511''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; UGA6P 2.2.362.2)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Seekmo 10.0.406.0)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.14eol) Gecko/20070505 (Debian-1.8.0.15~pre080323b-0etch2) Epiphany/2.14''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Arcor 5.004)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1pre) Gecko/2008062212 Firefox/3.0.1pre (Swiftfox)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.14) Gecko/20080404 Iceweasel/2.0.0.14 (Debian-2.0.0.14-2)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9) Gecko/2008061017 Firefox/3.0''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008052912 Firefox/3.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9) Gecko/2008052906 Firefox/3.0''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9b4pre) Gecko/2008022910 Viewzi/0.1''',
    '''Mozilla/4.78[en](X11;U;Linux 2.4.10-4GB i686)''',
    '''Mozilla/5.0 (X11; U; Linux i686; rv:1.8.1.13) Gecko/20080316''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.14eol) Gecko/20070505 Iceape/1.0.9 (Debian-1.0.13~pre080323b-0etch3)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2pre) Gecko/2008070420 Firefox/3.0.2pre (Swiftfox)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008070206 Firefox/3.0.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR={9B2CB79D-F2D8-4F97-AB28-3A8069923F22}; Media Center PC 3.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; FDM; .NET CLR 2.0.50727; MS-RTC LM 8)''',
    '''Opera/9.51 (Windows NT 5.1; U; en)''',
    '''Opera/9.51 (X11; Linux x86_64; U; en)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2pre) Gecko/2008072611 Firefox/3.0.2pre (Swiftfox)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9) Gecko/2008062910 Iceweasel/3.0 (Debian-3.0~rc2-2)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 3.0.04506.30; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648)''',
    '''Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.0.1) Gecko/2008082201 Firefox/3.0.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SU 3.011; FunWebProducts; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)''',
    '''Opera/9.52 (X11; Linux x86_64; U; en)''',
    '''Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.8.1.4) Gecko/20080721 BonEcho/2.0.0.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008072820 Firefox/3.0.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en; rv:1.9.0.1) Gecko/20080528 Epiphany/2.22 Firefox/3.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b1pre) Gecko/20080903034741 Minefield/3.1b1pre''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1a2) Gecko/20080829082037 Shiretoko/3.1a2''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en) AppleWebKit/522.11.1 (KHTML, like Gecko) Version/3.0 Safari/522.11.1''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.1) Gecko/2008071420 Iceweasel/3.0.1 (Debian-3.0.1-1)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.29 Safari/525.13''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071618 Iceweasel/3.0.1 (Debian-3.0.1-1)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.4; en-US; rv:1.9.0.1) Gecko/2008070206 Firefox/3.0.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.0; Windows NT 5.1; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; FDM; .NET CLR 1.1.4322; .NET CLR 3.5.21022; WWTClient2; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; WinNT4.0; en-US; rv:1.8.1.17) Gecko/20080829 SeaMonkey/1.1.12''',
    '''Mozilla/5.0 Gecko/2008071708 Firefox/3.0.0.1''',
    '''Mozilla/5.0 (Windows; U; WinNT3.51; en-US; rv:1.8.1.17) Gecko/20080829 SeaMonkey/1.1.12''',
    '''Mozilla/5.0 (Windows; U; WinNT4.0; en-US; rv:1.2b) Gecko/20020923 Phoenix/0.1''',
    '''Mozilla/5.0 [en] (Win95; I)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; MRA 5.1 (build 02243); MRSPUTNIK 2, 0, 0, 36 SW; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Iron/0.2.152.0 Safari/12273232.525''',
    '''Mozilla/4.8 [en] (WinNT; U)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:1.9.0.2) Gecko/2008091620 Firefox/3.0.2''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.2) Gecko/2008091620 Firefox/3.0.2''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.1) Gecko/2008070208 Firefox/3.0.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:1.8.1.17) Gecko/20080829 SeaMonkey/1.1.12''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.30 Safari/525.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.16) Gecko/20080702 SeaMonkey/1.1.11''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.2.153.1 Safari/525.19''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.0; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.2) Gecko/2008091620 Firefox/3.0.2''',
    '''Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.8.1.16) Gecko/20080702 Iceweasel/2.0.0.16 (Debian-2.0.0.16-0etch1)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; rv:1.9.0.3) Gecko/2008092417 Ubuntu/8.10 (Intrepid) Firefox/3.0.3''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.10 (intrepid) Firefox/3.0.3''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008092816 Iceweasel/3.0.3 (Debian-3.0.3-2)''',
    '''Mozilla/4.61 [ja] (X11; I; Linux 2.2.13-33cmc1 i686)''',
    '''Opera/9.61 (X11; Linux x86_64; U; en) Presto/2.1.1''',
    '''Mozilla/5.0 Gecko/2008092417 Firefox/3.0.3''',
    '''Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.9.0.3) Gecko/2008092416 Firefox/3.0.3''',
    '''Opera/9.52 (Windows NT 5.1; U; en)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_4_11; nl-nl) AppleWebKit/528.1 (KHTML, like Gecko) Version/4.0 Safari/528.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008092510 Ubuntu/8.04 (hardy) Firefox/3.0.3''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows NT 4.0; U) [en]''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008092816 Iceweasel/3.0.1 (Debian-3.0.1-1)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-GB; rv:1.9.0.4) Gecko/2008102920 Firefox/3.0.4''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008101315 Ubuntu/8.10 (intrepid) Firefox/3.0.3''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008092816 Iceweasel/3.0.3 (Debian-3.0.3-3)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.4) Gecko/2008111922 GranParadiso/3.0.4''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; GTB5; SIMBAR={AC95C400-1820-4258-B6BA-BD4CFF08F512})''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.4) Gecko/2008111317 Ubuntu/8.04 (hardy) Firefox/3.0.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/528.5 (KHTML, like Gecko) Iron/0.4.155.0 Safari/528.5''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.4) Gecko/2008111318 Ubuntu/8.04 (hardy) Firefox/3.0.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.4) Gecko/2008102920 Firefox/3.0.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.4) Gecko/2008102920 Firefox/3.0.4''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_2; en-us) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5''',
    '''Mozilla/5.0 (en-US) Firefox/3.0.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.36 Safari/525.19''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.43 Safari/525.19''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.5) Gecko/2008121622 Ubuntu/8.10 (intrepid) Firefox/3.0.5''',
    '''Opera/8.54 (Windows NT 5.0; U; en)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; GMX AG by USt; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.14eol) Gecko/20070505 (Debian-1.8.0.15~pre080614i-0etch1) Galeon/2.0.2 (Debian package 2.0.2-4)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.8.1.19) Gecko/20081217 Fedora/1.1.14-1.fc10 SeaMonkey/1.1.14''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.13) Gecko/20080311 (Debian-1.8.1.13+nobinonly-0ubuntu1) Kazehakase/0.5.2''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.18) Gecko/20081030 Iceweasel/2.0.0.18 (Debian-2.0.0.18-0etch1)''',
    '''Opera/10.00 (Windows NT 5.1; U; en) Presto/2.2.0''',
    '''Opera/9.63 (Windows NT 5.1; U; en) Presto/2.1.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b1) Gecko/20081007 Firefox/3.1b1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2a1pre) Gecko/20081227 Minefield/3.2a1pre''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.19) Gecko/20081204 Iceape/1.1.14 (Debian-1.1.14-1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1a1) Gecko/2008072310 Shiretoko/3.1a1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.27.1 (KHTML, like Gecko) Version/3.2.1 Safari/525.27.1''',
    '''Opera/9.63 (X11; Linux i686; U; en-GB) Presto/2.1.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.4.154.33 Safari/525.19''',
    '''Opera/10.00 (X11; Linux i686 ; U; en) Presto/2.2.0''',
    '''Mozilla/4.0 (compatible; MSIE 4.01; Windows NT)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/528.8 (KHTML, like Gecko) Chrome/2.0.156.1 Safari/528.8''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2a1pre) Gecko/20081206 Minefield/3.2a1pre''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b3pre) Gecko/20081202 SeaMonkey/2.0a2''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008100716 Firefox/3.0.3 Flock/2.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.19) Gecko/20081204 SeaMonkey/1.1.14''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.46 Safari/525.19''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20070321 Netscape/8.1.3''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1b2) Gecko/20081201 Firefox/3.1b2''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2a1pre) Gecko/20090130 Minefield/3.2a1pre''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-us) AppleWebKit/525.27.1 (KHTML, like Gecko) Version/3.2.1 Safari/525.27.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1a1) Gecko/2008072306 Shiretoko/3.1a1''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.0.5) Gecko/2008120121 Firefox/3.0.5''',
    '''Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.8.1.11) Gecko/20080213 SeaMonkey/1.1.7''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.48 Safari/525.19''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en-US; rv:1.8.0.7) Gecko/20060911 Camino/1.0.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2; Win64; x64; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; OfficeLiveConnector.1.3; OfficeLivePatch.1.3; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.48 Safari/525.19''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.4) Gecko/20030827 Debian/1.4-3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/530.1 (KHTML, like Gecko) Chrome/2.0.169.1 Safari/530.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ar; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020414 CentOS/3.0.6-1.el5.centos Firefox/3.0.6''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en; rv:2.0.0.0) Gecko/2009040101 Gentoo Firefox/4.0a1''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; MSN OptimizedIE8;DEDE)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko/2009032711 Ubuntu/8.10 (intrepid) Firefox/3.0.8''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.8''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.8) Gecko/2009033008 GranParadiso/3.0.8''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko/2009033017 GranParadiso/3.0.8''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; GTB5)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19''',
    '''Mozilla/5.0 (compatible; Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2) Gecko/20070219''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.6 Safari/530.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.9) Gecko/2009040821 Firefox/3.0.9''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020409''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042315 Firefox/3.0.10''',
    '''Opera/9.64 (Windows NT 6.0; U; pt) Presto/2.1.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009052212 Gentoo Firefox/3.0.10''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.10) Gecko/2009042809 GranParadiso/3.0.10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.28 Safari/530.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.10) Gecko/2009042523 Ubuntu/9.04 (jaunty) Firefox/3.0.10 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.10) Gecko/2009042810 GranParadiso/3.0.10''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; WOW64; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)''',
    '''Opera/9.80 (Windows NT 6.0; U; en) Presto/2.2.15 Version/10.00''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.28 Safari/530.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.30 Safari/530.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b1pre) Gecko/20080909032504 Minefield/3.1b1pre''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/531.0 (KHTML, like Gecko) Chrome/3.0.182.3 Safari/531.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.11) Gecko/2009060215 Firefox/3.0.11 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en; rv:1.9.0.11) Gecko/20080528 Epiphany/2.22''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.33 Safari/530.5''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.11) Gecko/2009060308 Ubuntu/9.04 (jaunty) Firefox/3.0.11''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; MRA 4.10 (build 01952); .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1) Gecko/20090701 Firefox/3.5''',
    '''Mozilla/5.0 (X11; U; IRIX IP22; en-US; rv:1.0.2) Gecko/20030820''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; OfficeLiveConnector.1.3; OfficeLivePatch.0.0; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1) Gecko/20090703 Shiretoko/3.5''',
    '''Opera/9.80 (Windows NT 5.1; U; en) Presto/2.2.15 Version/10.00''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; Arcor 5.006; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506; Media Center PC 5.0)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.6) Gecko/2009011913 Firefox''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; WOW64; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 1.1.4322; .NET CLR 3.5.30729; OfficeLiveConnector.1.4; OfficeLivePatch.1.3; .NET CLR 3.0.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.5 (KHTML, like Gecko) Chrome/2.0.172.37 Safari/530.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; el; rv:1.9.0.11) Gecko/2009060215 Firefox/3.0.11 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en) AppleWebKit/526.9 (KHTML, like Gecko) Version/4.0dp1 Safari/526.8''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1) Gecko/20090624 Firefox/3.5''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Safari/530.17''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-us) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Safari/530.17''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/525.28.3 (KHTML, like Gecko) Version/3.2.3 Safari/525.28.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-us) AppleWebKit/525.28.3 (KHTML, like Gecko) Version/3.2.3 Safari/525.28.3''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X; en) AppleWebKit/419 (KHTML, like Gecko) Safari/419.3''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.0.10) Gecko/2009042315 Firefox/3.0.10''',
    '''Opera/9.64 (Macintosh; Intel Mac OS X; U; en) Presto/2.1.1''',
    '''Opera/9.64 (Windows NT 6.0; U; en) Presto/2.1.1''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Iron/3.0.197.0 Safari/532.0''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.11) Gecko GranParadiso/3.0.11''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; GTB6; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; FDM; .NET CLR 3.0.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.5) Gecko/20060127 Netscape/8.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; cs-CZ; rv:1.7.12) Gecko/20050929''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.12) Gecko/2009070811 Ubuntu/9.04 (jaunty) Firefox/3.0.12''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Iron/3.0.197.0 Safari/532.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; cs; rv:1.9.0.8) Gecko/2009032609 Firefox/3.0.8 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; UCLBC)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.13) Gecko/2009080315 Linux Mint/7 (Gloria) Firefox/3.0.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; AllgÃ¤uer Medien Zentrum)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en; rv:1.9.0.13) Gecko/20080528 Epiphany/2.22''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; rv:1.9.0.14) Gecko/2009090217 Firefox/3.0.14''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; Mozilla/4.0 (compatible; MSIE 8.0; Win32; GMX); .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en; rv:1.9.0.14) Gecko/20080528 Epiphany/2.22''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.207.0 Safari/532.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.21 Safari/532.0''',
    '''Mozilla/4.05 [en] (X11; I; OSF1 V4.0 alpha)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.1 (KHTML, like Gecko) Chrome/4.0.213.1 Safari/532.1''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; WOW64; Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090919 Gentoo Firefox/3.5.3''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; GTB6.4; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.1 (KHTML, like Gecko) Chrome/5.0.322.2 Safari/533.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/533.1 (KHTML, like Gecko) Chrome/5.0.322.2 Safari/533.1''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; FDM)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; AskBar 3.00; ZangoToolbar 4.8.2)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-us) AppleWebKit/531.9 (KHTML, like Gecko) Version/4.0.3 Safari/531.9''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1; FDM; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100204 Gentoo Firefox/3.6''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; (R1 1.5); SpamBlockerUtility 4.7.1; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; CDSource=v9e.05)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; ZangoToolbar 4.8.3)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 GTB5''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Iron/3.0.197.0 Safari/532.0''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; (R1 1.1); ZangoToolbar 4.8.2; SpamBlockerUtility 4.8.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Neostrada TP 6.1; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.2.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; IEMB3; IEMB3; yplus 5.1.04b)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727; SpamBlockerUtility 4.8.4; ZangoToolbar 4.8.3)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1036 Safari/532.5''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR={742E5667-20B3-49c6-B7C7-A611183DCF3F}; (R1 1.5); .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; IEMB3)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; SLCC1; .NET CLR 1.1.4322; .NET CLR 2.0.40607; .NET CLR 3.0.04506.648)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9.2) Gecko/20100115 Firefox/3.6 GTB6''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 1.1.4325; .NET CLR 2.0.40607; .NET CLR 3.0.04506.648)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 1.1.4322; .NET CLR 3.5.30729; .NET CLR 3.0.30729; OfficeLiveConnector.1.4; OfficeLivePatch.1.3)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100301 Ubuntu/9.10 (karmic) Firefox/3.6''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.18) Gecko/2010020220 ${USR_AGNT} Firefox/3.0.18 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.10pre) Gecko/20100326 Ubuntu/9.10 (karmic) Shiretoko/3.5.8pre''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.0.3; .NET CLR 1.1.4322; yplus 5.1.04b)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en; rv:1.9.0.18) Gecko/20080528 Epiphany/2.22''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.21022; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.2.0; FunWebProducts; .NET CLR 1.1.4322; ZangoToolbar 4.8.3; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; id; rv:1.9.2) Gecko/20100115 Firefox/3.6''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1045 Safari/532.5''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20091020 Ubuntu/9.10 (karmic) Firefox/3.5.3''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; ADVPLUGIN|K114|03|S-659636590|dial; ADVPLUGIN|K114|03|S-659636590|dialno; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; GTB6.4)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; FunWebProducts; SIMBAR={833D4A5E-749E-11DC-88BE-0019B9606FF5}; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.0.04506)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.8) Gecko/20100312 Iceweasel/3.5.8 (like Firefox/3.5.8)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.2.0; FunWebProducts; .NET CLR 1.1.4322; HbTools 4.7.7; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; yplus 5.3.03b)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; {384E6D2F-3389-5FCF-2273-91E14AB57FD5}; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.18) Gecko/2010021501 Ubuntu/9.04 (jaunty) Firefox/3.0.18''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/4.0; GTB6; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0)''',
    '''Opera/9.82 (OpenMilleniumOS 9.1; U; GB) Presto/2.5.22 Version/12.03''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; E-nrgyPlus; dial; .NET CLR 1.0.3705)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; DigExt; MSN 8.0; MSN 8.5; MSNbMSNI; MSNmen-us; MSNcOTH)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Arcor 5.003; GTB6.4; .NET CLR 1.0.3705; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1045 Safari/532.5''',
    '''Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9.0.18) Gecko/2010021501 Ubuntu/8.04 (hardy) Firefox/3.0.18''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; TB Newsbar; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727; PeoplePal 3.0)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1064 Safari/532.5''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.23 Safari/533.4''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR Enabled; SIMBAR={8F36CAE7-A501-4364-B134-16BBEFBC3A06}; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Q312461; Cox High Speed Internet Customer; (R1 1.5); IEMB3; IEMB3)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; sbcydsl 3.12; ESB{182311D9-B95C-499B-A3AA-D275B80D1D45}; ESB{330CC175-CFAC-4875-BA5E-8FB31F15996F}; YPC 3.2.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; yplus 5.1.04b)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Zango 10.0.314.0)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1064 Safari/532.5''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; GTB6.4; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; OfficeLiveConnector.1.4; OfficeLivePatch.1.3; .NET4.0C; .NET4.0E)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.0; Windows NT 5.1; Media Center PC 3.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 3B 2.3)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.3) Gecko/20100419 Gentoo Firefox/3.6.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1064 Safari/532.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; generic_01_01; .NET CLR 1.0.3705; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.9) Gecko/20100401 Linux Mint/8 (Helena) <script>alert (document.cookie);</script>''',
    '''Mozilla/5.0 (en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; iebar; (none); (R1 1.5))''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.2 (KHTML, like Gecko) Chrome/5.0.342.9 Safari/533.2''',
    '''Mozilla/4.7 [de] (WinNT; I) [Netscape]''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; Win64; x64; en-US; rv:1.9.3a5pre) Gecko/20100602 Firefox/3.7a5pre''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; {0F47802C-547B-437A-B13A-B4B2CA09FE27}; .NET CLR 1.1.4322; .NET CLR 1.0.3705; Creative ZENcast v1.02.10; SpamBlockerUtility 4.8.4)''',
    '''Mozilla/5.0 (compatible; MSIE 7.0b; Windows NT 6.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SLCC1; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 ( .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Tablet PC 1.7; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; FunWebProducts; GTB6.5; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; GTB0.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; AskTB5.5)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; snprtz|S04045454802726; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.70 Safari/533.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Creative; .NET CLR 1.1.4322; .NET CLR 2.0.50727; IEMB3; PeoplePal 3.0; .NET CLR 3.0.04506.30; IEMB3)''',
    '''Opera/10.60 (Windows NT 5.1; U; cs) Presto/2.6.30 Version/10.60''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.70 Safari/533.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.70 Safari/533.4''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; IEMB3; SpamBlockerUtility 4.8.0; IEMB3)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.0.0; (R1 1.5); .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR={F65358C8-496C-4b9b-8FD4-001EECBE86F8}; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Creative ZENcast v1.02.11)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 3.1; IEMB3; HbTools 4.8.2; IEMB3)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Sgrunt|V109|301|S2025837643|dialno; Sgrunt|V109|301|S2025837643|dial; SIMBAR={32F4A5F6-F67C-40a2-9E8A-734147AC6639}; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; Media Center PC 5.1; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.4) Gecko/20100630 Gentoo Namoroka/3.6.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.5) Gecko/20100615 Firefox/3.6.5pre Fennec/1.1''',
    '''Opera/9.80 (Windows NT 6.1; U; en) Presto/2.6.30 Version/10.60''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.19) Gecko/2010091808 Iceweasel/3.0.9 (Debian-3.0.9-1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.59 Safari/534.3''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Media Center PC 3.0; .NET CLR 1.0.3705; IEMB3; .NET CLR 2.0.50727; HbTools 4.8.4; IEMB3)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; nb-NO; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2; WOW64; Trident/4.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET4.0C; .NET4.0E; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; Creative AutoUpdate v1.40.04)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.21022; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; GTB6.5; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Opera/9.80 (Windows NT 5.0; U; en) Presto/2.2.15 Version/10.20''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; )''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; GTB6.5; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 1.1.4322; .NET CLR 3.5.21022; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; ESB{6DE67919-89F5-42A2-B2E1-3E435A56D687}; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; ru-RU; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)''',
    '''Opera/9.80 (Windows NT 6.1; U; en) Presto/2.6.30 Version/10.62''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.544.0 Safari/534.10''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.10) Gecko/20100915 Ubuntu/10.04 (lucid) Firefox/3.6.10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; GTB6.5; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727; Creative ZENcast v1.01.06)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b6) Gecko/20100101 Firefox/4.0b6''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.0 Safari/534.10''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; SeekmoToolbar 4.8.4)''',
    '''Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.536.2 Safari/534.10''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-us) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727; ZangoToolbar 4.8.3; .NET CLR 3.0.04506.30)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/4.0; GTB6.5; SIMBAR={38A1F377-C71C-11DF-BDC9-00245417C23F}; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; OfficeLiveConnector.1.3; OfficeLivePatch.0.0)''',
    '''Mozilla/5.0 (Windows NT 5.1; U; en) Opera 8.01''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; .NET CLR 1.1.4322; .NET CLR 1.0.3705; MSN 9.0;MSN 9.1; MSNbQ002; MSNmen-us; MSNcOTH)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.14) Gecko/2009090216 Ubuntu/9.04 (jaunty) Firefox/3.0.14''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; Dealio Toolbar 3.1.1; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.9) Gecko/20100924 Gentoo Namoroka/3.6.9''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.86 Safari/533.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; SIMBAR Enabled; SIMBAR={A0FA34AC-A412-4983-838C-676D1C963DF7}; GTB6; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.11) Gecko/20101019 Firefox/3.6.11''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.9) Gecko/20100921 Gentoo Firefox/3.6.9''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.9) Gecko/20101005 Gentoo Firefox/3.6.9''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.15) Gecko/20101026 Firefox/3.5.15 ( .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; Linux i686; rv:2.0b6) Gecko/20100101 Firefox/4.0b6''',
    '''Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.44 Safari/534.7''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.44 Safari/534.7''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.10 (maverick) Firefox/3.6.12''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; GTB6.6; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; AskTbDVSV5/5.9.1.14019)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SU 2.010; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Media Center PC 5.0; SLCC1; Tablet PC 2.0; FDM; OfficeLiveConnector.1.5; OfficeLivePatch.1.3; .NET4.0C)''',
    '''Mozilla/4.76 [en] (Windows NT 5.0; U)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.44 Safari/534.7''',
    '''Opera/9.80 (Windows NT 6.1; U; en) Presto/2.6.30 Version/10.63''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.44 Safari/534.7''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101102 Gentoo Firefox/3.6.12''',
    '''Mozilla/5.0 Firefox/3.6.8''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.04 (lucid) Firefox/3.6.12''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Iron/6.0.475 Chrome/6.0.475.0 Safari/60814784.534''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.2.2) Gecko/20100316 MRA 5.6 (build 03278) Firefox/3.6.2 (.NET CLR 3.5.307''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 ( .NET CLR 3.5.30729; .NET4.0E)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; DigExt; MEGAUPLOAD 1.0)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; AskTB5.6)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; GTB6.6; .NET CLR 1.1.4322; .NET CLR 3.0.04506.30; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b7) Gecko/20100101 Firefox/4.0b7''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.12 (KHTML, like Gecko) Chrome/9.0.587.0 Safari/534.12''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:2.0b7) Gecko/20100101 Firefox/4.0b7''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.210 Safari/534.10''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; WOW64; Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET4.0C; .NET CLR 3.0.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; FunWebProducts; Ant.com Toolbar 1.6; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Iron/7.0.520.0 Chrome/7.0.520.0 Safari/534.7''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.15) Gecko/2009102814 Ubuntu/8.10 (intrepid) Firefox/3.0.15''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10''',
    '''Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.5; Trident/4.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 GTB7.1 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.2.0; FunWebProducts; Media Center PC 3.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 1.1.4322; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 ( .NET CLR 3.5.30729; .NET4.0E)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Ubuntu/10.04 Chromium/8.0.552.215 Chrome/8.0.552.215 Safari/534.10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.10 Safari/534.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10''',
    '''Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b6pre) Gecko/20100903 Firefox/4.0b6pre''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10''',
    '''Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 ImageShackToolbar/5.2.4 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; tr; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/534.10''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 1&1 Internet Inc. by USt; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.2.13) Gecko/20101203 MRA 5.7 (build 03790) Firefox/3.6.13 ( .NET CLR 3.5.30729) sputnik 2.3.1.118''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; ru-ru) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.53 Safari/534.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; tr; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.04 (lucid) Firefox/3.6.13''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101118 Gentoo Firefox/3.6.12''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/534.10''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.15) Gecko/20101028 Iceweasel/3.5.15 (like Firefox/3.5.15)''',
    '''Mozilla/5.0 (X11; U; Linux i686; tr-TR; rv:1.9.2.12) Gecko/20101028 Pardus/2009 Firefox/3.6.12''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.13) Gecko/20101203 AskTbUT2V5/3.9.1.14019 Firefox/3.6.13''',
    '''Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/532.4 (KHTML, like Gecko) Qt/4.6.3 Safari/532.4''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.603.3 Safari/534.14''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; OfficeLiveConnector.1.4; OfficeLivePatch.1.3; .NET4.0C; .NET4.0E)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB6.5; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; WOW64; FunWebProducts)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.19 Safari/534.13''',
    '''Mozilla/5.0 (Windows; 0; Windows NT 6.1; rv:1.9.2.13) Gecko/20101203''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19''',
    '''Mozilla/4.0 (compatible; ICS)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR={8DD73202-C28F-45A5-8DC8-552182FE3DC7}; GTB6.5; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b8) Gecko/20100101 Firefox/4.0b8''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 3.0.04506.30; .NET CLR 2.0.50727; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SIMBAR={DF68E357-475E-4DFD-921B-A7D64B58D8A3}; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; MATM)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Chrome/10.0.612.1 Safari/534.15''',
    '''Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SBC; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1059 Safari/532.5''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100405 Namoroka/3.6.3''',
    '''Mozilla/5.0 (X11; U; Linux; en-US; rv:1.9.2.12) Gecko/20101206 Firefox/3.6.12''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-TW; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 ( .NET CLR 3.5.30729; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; eSobiSubscriber 2.0.4.16; .NET4.0C)''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:2.0b8) Gecko/20100101 Firefox/4.0b8''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; MSN 6.1; MSNbMSFT; MSNmen-us; MSNczz; MSNc11)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; CMDTDF)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; nl; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101230 Firefox/3.6.13''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; AskTbWIZ/5.8.0.12304)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Iron/8.0.555.0 Chrome/8.0.555.0 Safari/534.10''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; GTB6.6; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; TOB 6.06; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 ( .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.30729; .NET CLR 3.5.30729; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; AT&T CSM8.0; .NET CLR 1.1.4322; yplus 5.1.04b)''',
    '''Opera/9.64(Windows NT 5.1; U; en) Presto/2.1.1''',
    '''Mozilla/4.76 [ru] (X11; U; SunOS 5.7 sun4u)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.14) Gecko/2009082707 Firefox/3.0.14 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.45 Safari/534.13''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.19 Safari/534.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.16) Gecko/20101130 AlexaToolbar/alxf-2.01 Firefox/3.5.16''',
    '''Opera/9.80 (Windows NT 5.1; U; en) Presto/2.7.62 Version/11.00''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.237 Safari/534.10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR={01CEDAA9-13DF-4acf-AFF7-6A9C825D92BB}; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Opera/9.80 (Macintosh; Intel Mac OS X; U; en) Presto/2.2.15 Version/10.00''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Iron/8.0.555.1 Chrome/8.0.555.1 Safari/534.10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 MRA 5.5 (build 02842) Firefox/3.5.6''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.15) Gecko/20101028 none none''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.237 Safari/534.10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.33 Safari/534.3 SE 2.X MetaSr 1.0''',
    '''Opera/9.80 (Windows NT 6.1; U; ru) Presto/2.7.62 Version/11.01''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Sgrunt|V109|301|S-527713550|dial; snprtz|T13562000000070|2600#Service Pack 2#2#5#1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; ru-RU; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YComp 5.0.2.4)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.237 Safari/534.10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; MEGAUPLOAD 1.0; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101203 AlexaToolbar/alxf-1.54 Firefox/3.6.13 GTB7.1''',
    '''Opera/9.80 (X11; Linux x86_64; U; en) Presto/2.7.62 Version/11.01''',
    '''Mozilla/5.0 (XP; U; NT 5.1; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 CNS_UA; AD_LOGON=4C47452E4E4554;''',
    '''Opera/9.64 (Windows NT 5.1; U; en) Presto/2.1.1''',
    '''Mozilla/5.0 (X11; Linux i686 on x86_64; rv:2.0b10) Gecko/20100101 Firefox/4.0b10''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.11 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101206 Ubuntu/9.10 (karmic) Firefox/3.6.13''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; Seekmo 11.0.117.0)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.84 Safari/534.13''',
    '''Opera 9.7 (Windows NT 5.2; U; en)''',
    '''Mozilla/4.79 [en] (Windows NT 5.0; U)''',
    '''Opera/9.80 (Windows NT 6.1; U; en) Presto/2.7.62 Version/11.01''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; .NET CLR 2.0.50727; Creative ZENcast v1.04.06)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 GTB7.1 ( .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10 ChromePlus/1.5.1.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16 ( .NET CLR 3.5.30729; .NET4.0E)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.19 Safari/534.13''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0b11) Gecko/20100101 Firefox/4.0b11''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; it-IT; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.94 Safari/534.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.98 Safari/534.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; id; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; GTB6.6; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30618; .NET4.0C)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101203 AskTbTRL2/3.9.1.14019 Firefox/3.6.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0E)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6''',
    '''Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; uk; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.102 Safari/534.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Win64; x64; Trident/4.0; GTB6.6; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.94 Safari/534.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; HbTools 4.7.7; .NET CLR 2.0.50727; IEMB3; IEMB3)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20101123 SeaMonkey/2.0.11''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13 gmx/1.5.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.0.3; .NET CLR 1.1.4322; yplus 4.1.00b)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 035217492''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.82 Safari/534.16''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; MRA 4.10 (build 01952); MRSPUTNIK 1, 8, 0, 17 SW; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.22 (KHTML, like Gecko) Ubuntu/10.10 Chromium/11.0.683.0 Chrome/11.0.683.0 Safari/534.22''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.98 Safari/534.13''',
    '''Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.2)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.0.3; FunWebProducts; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0; GTB6; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR Enabled; SIMBAR={A0339C60-71EB-42f9-AEBE-9D82FBC21B60}; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.14) Gecko/20110218 Firefox/3.6.14 (.NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (X11; U; OpenBSD amd64; en-US; rv:1.9.2.13) Gecko/20110120 Firefox/3.6.13''',
    '''Opera/9.80 (Windows NT 5.1; U; en) Presto/2.7.62 Version/11.01''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.107 Safari/534.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; ZangoToolbar 4.8.3; MSN 6.1; MSNbMSFT; MSNmen-au; MSNc00; v5m)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10''',
    '''Opera/9.80 (Windows NT 5.1; U; hu) Presto/2.7.62 Version/11.01''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; GTB6.6; .NET CLR 2.0.50727)''',
    '''Opera/9.80 (Windows NT 5.1; U; en) Presto/2.6.30 Version/10.62''',
    '''Mozilla/6.0 (compatible; MSIE 7.0a1; Windows NT 5.2; SV1)''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:2.0b12) Gecko/20100101 Firefox/4.0b12''',
    '''Mozilla/5.0 (Windows NT 6.0; rv:2.0b12) Gecko/20100101 Firefox/4.0b12''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.17.8 (KHTML, like Gecko) Version/5.0.1 Safari/533.17.8''',
    '''Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.2; WOW64; Trident/5.0)''',
    '''Mozilla/4.0 (compatible;MSIE 7.0;Windows NT 6.1)''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0b12) Gecko/20100101 Firefox/4.0b12''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Chrome/10.0.612.1 Safari/534.15''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; AskTbDSGOH/5.9.1.14019)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET4.0C; .NET CLR 3.0.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; MathPlayer 2.10a; .NET CLR 1.1.4322; .NET CLR 1.0.3705; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Opera/9.80 (Windows NT 5.1; U; en) Presto/2.6.30 Version/10.63''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; sv-SE; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15 ( .NET CLR 3.5.30729; .NET4.0C)''',
    '''Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.9.0.16) Gecko/2009122206 Firefox/3.0.16 Flock/2.5.6''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.2.0; FunWebProducts-MyWay; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 1.1.4322; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16''',
    '''Mozilla/5.0 (Windows NT 5.1; U) Opera 8.51 [de]''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; FDM; .NET CLR 3.0.04506.30; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.702.0 Chrome/12.0.702.0 Safari/534.24''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Opera/9.80 (Windows NT 5.1; U; MRA 5.7 (build 03797); ru) Presto/2.7.62 Version/11.01''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/528.7 (KHTML, like Gecko) Iron/1.0.155.0 Safari/528.7''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET CLR 1.1.4322; Media Center PC 5.0; SLCC1; .NET4.0C)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.151 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.151 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0b13pre) Gecko/20110316 Firefox/4.0b13pre''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.151 Safari/534.16''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; SIMBAR={EE6EC1BC-4971-484E-9822-4C4E7D3B4480}; GTB6.6; FunWebProducts; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15 ( .NET CLR 3.5.30729; .NET4.0E)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.16pre) Gecko/20110310 Ubuntu/10.10 (maverick) Namoroka/3.6.16pre''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 3.1; IEMB3)''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0.0) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Iron/9.0.600.2 Chrome/9.0.600.2 Safari/534.13''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.1 SUSE/6.0.443.0 (KHTML, like Gecko) Chrome/6.0.443.0 Safari/534.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.151 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.16) Gecko/20110323 Ubuntu/10.10 (maverick) Firefox/3.6.16''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; AskTbDSGOH/5.11.3.15590)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.464.0 Safari/534.3''',
    '''Mozilla/5.0 (Windows NT 6.0; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/4.61 [en] (X11; U; ) - BrowseX (2.0.0 Windows)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.99 Safari/533.4''',
    '''Mozilla/5.0 (X11; U; OpenVMS COMPAQ_Professional_Workstation; en-US; rv:1.8.1.17) Gecko/20081029 SeaMonkey/1.1.12''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; GTB6.6; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30618; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.33 Safari/534.3 SE 2.X MetaSr 1.0''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; {24FAD8A4-B663-EA51-14C7-203047DAFEB9}; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; OfficeLiveConnector.1.3; OfficeLivePatch.0.0; MAAU; .NET4.0C)''',
    '''Mozilla/5.0 (X11; Linux i686; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.3) Gecko/20073310 Iceweasel/2.0.0.3 (Debian-2.0.0.3-1)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; at; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Hotbar 4.5.1.0; FunWebProducts; .NET CLR 1.0.3705)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.18) Gecko/20110319 Firefox/3.5.18''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SU 3.26; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Tablet PC 2.0; .NET4.0C; OfficeLiveConnector.1.5; OfficeLivePatch.1.3; .NET4.0E)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; tr; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.27 (KHTML, like Gecko) Chrome/12.0.719.0 Safari/534.27''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101203 AskTbPLTV5/3.8.0.12304 Firefox/3.6.13''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20110401 Netshakexploder/4.11.31''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; (R1 1.5); Media Center PC 3.0; .NET CLR 1.0.3705; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20110401 NetshakeExploder/4.11.31''',
    '''Mozilla/5.0 (Windows NT 6.0; WOW64; rv:2.0) Gecko/20100101 Firefox/{Pulse Code Communications}''',
    '''Mozilla/5.0 (Windows NT 6.1.7850.0.winmain_win8m1.100922-1508; WOW128; rv:2.0) Gecko/2011-04-01''',
    '''Mozilla/5.0 (Windows; OMG unique user agent''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.205 Safari/534.16''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Tablet PC 2.0; .NET4.0C; Creative AutoUpdate v1.40.01)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.16) Gecko/20110408 Gentoo Firefox/3.6.16''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.205 Safari/534.16''',
    '''Mozilla 5./0 (compatible) Opera or Gecko''',
    '''Mozilla/5.0 compatible; MSIE 7.0; Windows NT 5.1''',
    '''Mozilla/5.0 (X11; Linux i686; U) Opera 11.10 [en]''',
    '''Mozilla/5.0 (X11; D; Linux i686; en; rv:1.9.2.3) Gecko/20100408 Ubuntu/8.10 (maverick) Firefox/3.6.13''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.31 (KHTML, like Gecko) Chrome/12.0.745.0 Safari/534.31''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.205 Safari/534.16''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:2.0) Gecko/20100101 Firefox/4.0 WebMoney Advisor''',
    '''Mozilla/5.0 (X11; Linux i686; rv:5.0a2) Gecko/20110423 Firefox/5.0a2''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; DigExt; AT&T CSM8.0; .NET CLR 2.0.50727)''',
    '''Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.10''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0) Gecko/20110321 Firefox/4.0''',
    '''Opera/9.80 (X11; Linux i686; U; en) Presto/2.8.131 Version/11.10''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8) Gecko/20051219 SeaMonkey/1.0b''',
    '''Mozilla/5.0 (Windows NT 5.1; U; en) Opera 8.00''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0a2) Gecko/20110426 Firefox/5.0a2''',
    '''Mozilla/4.8 [en] (Windows NT 5.0; U)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20121221 Firefox/3.6.8''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.60 Safari/534.24''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.60 Safari/534.24''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; GTB6.3; QS 4.2.4.0; QS 5.1.2.1; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; QS 4.2.4.0; QS 5.1.2.1)''',
    '''Mozilla/5.0 (Windows NT 6.1) Gecko/20100101 Firefox/4.0''',
    '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.12 Safari/534.30''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.57 Safari/534.24''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; Tablet PC 2.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; .NET CLR 1.1.4322; MSN 9.0; MSNbMSNI; MSNmen-us; MSNcIA; MPLUS)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.57 Safari/534.24''',
    '''Mozilla/5.0 (Windows NT 6.0; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.16) Gecko/20110329 Gentoo Firefox/3.6.16''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; .NET CLR 1.0.3705; .NET CLR 2.0.50727; .NET CLR 1.1.4322; Media Center PC 4.0; SpamBlockerUtility 4.8.4)''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.60 Safari/534.24''',
    '''Mozilla/4.0 (compatible; MSIE 3.0; Windows NT; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.8 (KHTML, like Gecko) Chrome/4.0.277.0 Safari/532.8''',
    '''Mozilla/5.0 (X11; Linux i686; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.125 Safari/533.4''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/11.0.696.57 Chrome/11.0.696.57 Safari/534.24''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.65 Safari/534.24''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.17) Gecko/20110420 Firefox/3.6.17 ( .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.65 Safari/534.24''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.0.3705; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; Creative ZENcast v2.00.07)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; MSN OptimizedIE8;DEDE)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Hotbar 4.4.9.0; (R1 1.5); .NET CLR 1.1.4322; IEMB3; IEMB3)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; snprtz|T05041833490253; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.65 Safari/534.24''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:2.0) Gecko/20110319 Firefox/4.0''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.53 Safari/534.30''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0.1) Gecko/20110430 Firefox/4.0.1 Iceweasel/4.0.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.68 Safari/534.24''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.68 Safari/534.24''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2; WOW64; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.597 Safari/534.14''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SIMBAR Enabled; SIMBAR={A6B3F725-664B-4b71-B4E6-AB1B7489CC72})''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.68 Safari/534.24''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; ShopperReports 3.0.517.0; SRS_IT_E8790770BC765C5A3EAD94)''',
    '''Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; MATM)''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/11.04 Chromium/11.0.696.68 Chrome/11.0.696.68 Safari/534.24''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Tablet PC 2.0)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TheFreeDictionary.com; ZangoToolbar 4.8.3)''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:5.0a2) Gecko/20110523 Firefox/5.0a2''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MDDR; .NET4.0C)''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.772.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 5.2; WOW64; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.8.131 Version/11.11''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:5.0a2) Gecko/20110524 Firefox/5.0a2''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.71 Safari/534.24''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.71 Safari/534.24''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.71 Safari/534.24''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0b13pre) Gecko/20110322 Firefox/4.0b13pre''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110527 Firefox/6.0a2''',
    '''Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.8.131 Version/11.11''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.68 Safari/534.30''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; GTB7.0; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.71 Safari/534.24''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 (.NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30618)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Application CD Build 2.0.0; FunWebProducts)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.16) Gecko/20110323 Ubuntu/10.10 (maverick) Firefox/3.6.16 GTB7.1''',
    '''Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.36 (KHTML, like Gecko) Chrome/13.0.767.1 Safari/534.36''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2; WOW64; Trident/4.0; .NET CLR 2.0.50727)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; GTB6.6; SLCC1; .NET CLR 2.0.50727; .NET CLR 1.1.4322; .NET CLR 3.5.30729; .NET CLR 3.0.30618; .NET4.0C)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 1.1.4322; .NET4.0C)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Iron/7.0.520.1 Chrome/7.0.520.1 Safari/534.7''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.17) Gecko/20110422 Linux (High Security System ) Firefox''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Trident/5.0)''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1/site-owner''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YComp 5.0.0.0; FunWebProducts; .NET CLR 1.0.3705; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows NT 5.2; WOW64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; SLCC1; .NET CLR 2.0.50727; .NET CLR 1.1.4322; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30''',
    '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 (KHTML, like Gecko) Ubuntu/10.04 Chromium/14.0.792.0 Chrome/14.0.792.0 Safari/535.1''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/11.0.696.68 Chrome/11.0.696.68 Safari/534.24''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; {FC5DA251-970F-FD5A-E748-17E0C6A6909A}; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (X11; Linux i686 on x86_64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; AskTB5.5)''',
    '''Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.17) Gecko/20110420 Firefox/3.6.17''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0.1) Gecko/20110430 Firefox/6.0''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1)''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:5.0) Gecko/20100101 Firefox/5.0 Iceweasel/5.0''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.100 Safari/534.30''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11 GTB7.1 ( .NET CLR 3.5.30729; .NET4.0E)''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1''',
    '''Opera/9.80 (X11; Linux x86_64; rv:2.0.1) Presto/2.8.131 Version/11.11''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.17) Gecko/20110420 Firefox/3.6.18''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:2.0.1) Gecko/20110506 Firefox/4.0.1''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Opera/9.80 (X11; Linux x86_64; U; en) Presto/2.8.131 Version/11.11''',
    '''Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 6.0 ; .NET CLR 2.0.50215; SL Commerce Client v1.0; Tablet PC 2.0''',
    '''Mozilla/5.0 (Windows NT 6.0; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; id; rv:1.9.2) Gecko/20100115 Firefox/3.6''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.17) Gecko/20110420 Firefox/3.6.17''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.18) Gecko/20110614 AlexaToolbar/alxf-2.13 Firefox/3.6.18''',
    '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.50 Safari/534.24''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; tr; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0E)''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.797.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.0; WOW64; rv:5.0) Gecko/20100101 Firefox/5.0; t.i.m.; pk; k.konzept;''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.2.18) Gecko/20110615 Ubuntu/10.04 (lucid) Firefox/3.6.18''',
    '''Mozilla/5.0 (Windows NT 5.0; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.803.0 Safari/535.1''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 1.1.4322; MS-RTC LM 8; msn OptimizedIE8;ENUS)''',
    '''Opera/9.80 (Windows NT 6.0; U; en) Presto/2.8.131 Version/11.11''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.4) Gecko/20100520 FireDownload/2.0.1 Firefox/3.6.4 Wyzo/3.6.4.1 FireTorrent/2.0.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_7) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.2; GTB7.0; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-us) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; FunWebProducts; .NET CLR 1.0.3705; .NET CLR 1.1.4322; Media Center PC 4.0; Badongo 2.0.0; SpamBlockerUtility 4.8.4)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; MDDC; .NET4.0C)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 6.0) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0a1) Gecko/20110705 Firefox/7.0a1''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.813.0 Safari/535.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.15) Gecko/20110303 Ultimate Edition/2.8 (maverick) Firefox/3.6.15''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.801.0 Safari/535.1''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; WebMoney Advisor; .NET4.0C; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 1.1.4322)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; MS-RTC LM 8; .NET4.0C; .NET4.0E; MS-RTC LM 8)''',
    '''Opera/9.80 (Windows NT 6.1; U; ru) Presto/2.6.30 Version/10.60''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0HTTcryPt/Add-on''',
    '''Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.9.168 Version/11.50''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.2) Gecko/20121223 Ubuntu/9.25 (jaunty) Firefox/3.8''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18) Gecko/20110628 Ubuntu/10.10 (maverick) Firefox/3.6.18''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; MSOffice 12)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2; Trident/4.0; .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; chromeframe/12.0.742.112; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; MDDR)''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2; Trident/4.0; .NET CLR 1.1.4322; .NET4.0C; .NET4.0E; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.18) Gecko/20110614 Firefox/3.6.18''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET CLR 1.1.4322)''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.122 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.122 Safari/534.30''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SpamBlockerUtility 4.8.4; ZangoToolbar 4.8.3)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.18) Gecko/20110614 Firefox/3.6.18''',
    '''Mozilla/5.0 (U; Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.122 Safari/534.30''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.41 Safari/535.1''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.124 Safari/534.30''',
    '''Opera/9.80 (X11; Linux x86_64; U; en) Presto/2.9.168 Version/11.50''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7''',
    '''Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; iOpus-Web-Automation)''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0.1) Gecko/20100101 Firefox/5.0.1''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.772.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.0; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.91 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.832.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:5.0.1) Gecko/20100101 Firefox/5.0.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.833.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:5.0.1) Gecko/20100101 Firefox/5.0.1''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 1.1.4322; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 3.5.30729)''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; QS 4.2.1.0)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.8 Safari/535.1''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.18) Gecko/20110628 Ubuntu/10.04 (lucid) Firefox/3.6.18''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Iron/6.0.475 Chrome/6.0.475.0 Safari/98995392.534''',
    '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.124 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.30 (KHTML, like Gecko) Iron/12.0.750.0 Chrome/12.0.750.0 Safari/534.30''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; tr-TR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.9 Safari/535.1''',
    '''Opera/9.80 (X11; Linux i686; U; en) Presto/2.9.168 Version/11.50''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.30 (KHTML, like Gecko) Iron/12.0.750.0 Chrome/12.0.750.0 Safari/534.30''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.19) Gecko/20110707 Firefox/3.6.19''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.742.124 Chrome/12.0.742.124 Safari/534.30''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:5.0.1) Gecko/20100101 Firefox/5.0.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.18) Gecko/20110628 Ubuntu/10.10 (maverick) Firefox/3.6.18''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/15.0.841.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/15.0.841.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.94 Safari/534.13''',
    '''Mozilla/5.0 (Windows NT 6.0) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.122 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/15.0.844.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/15.0.844.0 Safari/535.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; MyIE2; mxie; Maxthon; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19''',
    '''Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.12) Gecko/20101026 cai lon gi cha duoc''',
    '''Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.16) Gecko/20110701 Iceweasel/3.5.16 (like Firefox/3.5.16)''',
    '''Mozilla/5.0 (X11; FreeBSD i386; rv:5.0) Gecko/20100101 Firefox/5.0''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.109 Safari/535.1''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.5; rv:2.0.1) Gecko/20100101 Firefox/4.0.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; YPC 3.2.0; .NET CLR 1.0.3705; Media Center PC 3.1; .NET CLR 1.1.4322; yplus 5.1.04b)''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/5.0 (X11; Linux armv7l) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.824.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.112 Safari/535.1''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; SV1; IEMB3; IEMB3)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.0.19) Gecko/2010031422 adsasdasdasd''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/15.0.848.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/15.0.848.0 Safari/535.1''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; GTB7.1; .NET CLR 2.0.50727)''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.112 Safari/535.1''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/15.0.849.0 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0a2) Gecko/20110814 Firefox/7.0a2''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; {5F2A1894-7E5F-4086-9F24-1BE5336B3AC5}; .NET CLR 1.1.4322; MSN 6.1; MSNbDELL; MSNmen-us; MSNc0z; MSNc00)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 ( .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (Windows NT 6.0; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/5.0 (compatible; U) AppleWebKit/533.1 (KHTML, like Gecko) Maxthon/3.0.8.2 Safari/533.1''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; vi; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.20) Gecko/20110803 Firefox/3.6.20''',
    '''Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; nl-nl) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.855.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.855.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.856.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.0; it; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; GTB6.6; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MDDR; .NET4.0C; MS-RTC LM 8)''',
    '''Mozilla/5.0 (Windows NT 5.1; rv:7.0) Gecko/20100101 Firefox/7.0''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.857.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/5.0 (X11; Linux x86_64; rv:8.0a2) Gecko/20110818 Firefox/8.0a2''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.859.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.854.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.112 Safari/535.1''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.20) Gecko/20110804 Red Hat/3.6.20-2.el6_1 Firefox/3.6.20''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1''',
    '''Mozilla/5.0 (X11; Linux i686; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_1) AppleWebKit/534.48.3 (KHTML, like Gecko) Version/5.1 Safari/534.48.3''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; chromeframe/13.0.782.112; GTB7.1; .NET CLR 2.0.50727; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 1.1.4322; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET4.0C; .NET4.0E)''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.30 (KHTML, like Gecko) Ubuntu/11.04 Chromium/12.0.742.112 Chrome/12.0.742.112 Safari/534.30''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.861.0 Safari/535.2''',
    '''Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.854.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1''',
    '''Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.1 (KHTML, like Gecko) Iron/13.0.800.0 Chrome/13.0.800.0 Safari/535.1''',
    '''Mozilla/5.0 (Macintosh; Intel Mac OS X 10.5; rv:6.0) Gecko/20100101 Firefox/6.0''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.20) Gecko/20110803 Firefox/3.6.20 GTB7.1 ( .NET CLR 3.5.30729)''',
    '''Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.20) Gecko/20110805 Linux Mint/10 (Julia) Firefox/3.6.20''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; GTB7.1; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)''',
    '''Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.20) Gecko/20110803 Firefox/3.6.20''',
    '''Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.865.0 Safari/535.2''',
    '''Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:x.x.x) Gecko/20041107 Firefox/x.x''',
    '''Mozilla/5.0 (Windows NT 6.1; rv:7.0) Gecko/20100101 Firefox/7.0''',
    '''Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; MS-RTC LM 8)''',
)

_r = None
def randua():
    '''Returns a User-Agent string randomly'''
    global _r
    if _r is None:
       import random
       from time import time
       _r = random.Random(time())
    return _r.choice(_uas)

# Mapping status codes to official W3C names
HTTP_STATUS_CODES = {
    100: 'Continue',
    101: 'Switching Protocols',

    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',

    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    306: '(Unused)',
    307: 'Temporary Redirect',

    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request-URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',

    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
}

def mb_code(s, coding=None):
    '''encoding/decoding helper'''

    if isinstance(s, unicode):
        return s if coding is None else s.encode(coding)
    for c in ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5'):
        try:
            s = s.decode(c, errors='replace')
            return s if coding is None else s.encode(coding, errors='replace')
        except: pass
    return s
