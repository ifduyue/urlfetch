#coding: utf8
#
#    urlfetch 
#    ~~~~~~~~
#
#    An easy to use HTTP client based on httplib.
#
#    :copyright: (c) 2011  Elyes Du.
#    :license: BSD, see LICENSE for more details.
#

__version__ = '0.3.5'
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
    'UrlfetchException',
] 

_allowed_methods = ("GET", "DELETE", "HEAD", "OPTIONS", "PUT", "POST", "TRACE", "PATCH")

class UrlfetchException(Exception): pass

def sc2cs(sc):
    '''convert response.getheader('set-cookie') to cookie string
    
    Args:
        sc (str): The Set-Cookie string
        you can get it from::

            >>> sc = response.getheader('Set-Cookie')
    
    Returns:
        str. cookie string, name=value pairs, joined by `'; '`
     
    '''
    c = Cookie.SimpleCookie(sc)
    sc = ['%s=%s' % (i.key, i.value) for i in c.itervalues()]
    return '; '.join(sc)


_boundary_prefix = None
def choose_boundary():
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
    

class Response(object):
    
    def __init__(self, r, **kwargs):
        self._r = r
        self.msg = r.msg
        self.status = r.status
        self.length = r.length
        self.reason = r.reason
        self.version = r.version
        self._body = None
        self._headers = None
        self._text = None

        self.getheader = r.getheader
        self.getheaders = r.getheaders
    
        if kwargs.get('prefetch', False):
            self._body = self._r.read()
        
        for k in kwargs:
            setattr(self, k, kwargs[k])
        
    @classmethod
    def from_httplib(cls, r, **kwargs):
        return cls(r, **kwargs)
        
    @property
    def body(self):
        if self._body is None:
            self._body = self._r.read()
        return self._body
    
    @property
    def text(self):
        if self._text is None:
            self._text = util.mb_code(self.body)
        return self._text
    
    @property
    def headers(self):
        if self._headers is None:
            self._headers = dict((k.lower(), v) for k, v in self._r.getheaders())
        return self._headers
        

def fetch(url, data=None, headers={}, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, 
            randua=True, files={}, auth=None, prefetch=True, host=None):
    ''' fetch url

    Args:
        url (str): url to fetch

    Kwargs:
        data (dict/str):  The post data, it can be dict or string

        headers (dict):   The request headers

        timeout (double): The timeout

        randua (bool): Use random User-Agent when this is True

        files (dict): key is field name, value is (filename, fileobj) OR simply fileobj.
                      fileobj can be a file descriptor open for read or simply string

        auth (tuple): (username, password) for basic authentication

        prefetch (bool): True for prefetching response body

        host (string): To specify the host, useful when the domain can resolve to many IPs


    Returns:
        response object

    .. note::
        Default headers: {'Accept': '\*/\*'}
    '''
    local = locals()
    if data is not None and isinstance(data, (basestring, dict)):
        return post(**local)
    return get(**local)



def request(url, method="GET", data=None, headers={},
            timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
            randua=True, files={}, auth=None, prefetch=True, host=None):
    ''' request a url

    Args:
        url (str): url to fetch

    Kwargs:
        method (str): The request method, 'GET', 'POST', 'HEAD', 'PUT' OR 'DELETE'
                      
        data (dict/str):  The post data, it can be dict or string

        headers (dict):   The request headers

        timeout (double): The timeout

        randua (bool): Use random User-Agent when this is True

        files (dict): key is field name, value is (filename, fileobj) OR simply fileobj.
                      fileobj can be a file descriptor open for read or simply string

        auth (tuple): (username, password) for basic authentication

        prefetch (bool): True for prefetching response body

        host (string): To specify the host, useful when the domain can resolve to many IPs

    Returns:
        response object

    .. note::
        Default headers: {'Accept': '\*/\*'}
    '''

    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    method = method.upper()
    if method not in _allowed_methods:
        raise UrlfetchException("Method shoud be one of " + ", ".join(_allowed_methods))

    requrl = path
    if query: requrl += '?' + query
    # do not add fragment
    #if fragment: requrl += '#' + fragment
    

    if ':' in netloc:
        _host, port = netloc.rsplit(':', 1)
        port = int(port)
    else:
        _host, port = netloc, None
    if host is None:
        host = _host
    
    if scheme == 'https':
        h = HTTPSConnection(host, port=port, timeout=timeout)
    elif scheme == 'http':
        h = HTTPConnection(host, port=port, timeout=timeout)
    else:
        raise UrlfetchException('Unsupported protocol %s' % scheme)
        
    reqheaders = {
        'Accept' : '*/*',
        'User-Agent': uas.randua() if randua else 'urlfetch/' + __version__,
    }

    if auth is not None: 
        if isinstance(auth, (list, tuple)):
            auth = '%s:%s' % tuple(auth)
        auth = base64.b64encode(auth.encode('utf-8'))
        reqheaders['Authorization'] = 'Basic ' + auth.decode('utf-8')

    if files:
        content_type, data = _encode_multipart(data, files)
        reqheaders['Content-Type'] = content_type
    elif isinstance(data, dict):
        data = urlencode(data)
    
    if isinstance(data, basestring) and not files:
        # httplib will set 'Content-Length', also you can set it by yourself
        reqheaders["Content-Type"] = "application/x-www-form-urlencoded"
        # what if the method is GET, HEAD or DELETE 
        # just do not make so much decisions for users

    for k, v in headers.items():
        reqheaders[k.title()] = v 
    
    h.request(method, requrl, data, reqheaders)
    response = h.getresponse()
    return Response.from_httplib(response, prefetch=prefetch, reqheaders=reqheaders)

# some shortcuts
get = partial(request, method="GET")
post = partial(request, method="POST")
put = partial(request, method="PUT")
delete = partial(request, method="DELETE")
head = partial(request, method="HEAD")
options = partial(request, method="OPTIONS")
trace = partial(request, method="TRACE")
patch = partial(request, method="PATCH")

