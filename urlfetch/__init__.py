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

__version__ = '0.1.11'
__author__ = 'Elyes Du <lyxint@gmail.com>'
__url__ = 'https://github.com/lyxint/urlfetch'


import httplib
from urllib import urlencode
import urlparse
import Cookie
from uas import randua
import base64
from functools import partial
from __init__ import __version__

__all__ = [
    'sc2cs', 'fetch', 'fetch2', 
    'get', 'head', 'put', 'post', 'delete'
] 

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


def fetch(url, data=None, headers={}, timeout=None, randua=True):
    ''' fetch url

    Args:
        url (str): url to fetch

    Kwargs:
        data (dict/str):  The post data, it can be dict or string

        headers (dict):   The request headers

        timeout (double): The timeout

        randua (bool): Use random User-Agent when this is True

    Returns:
        response object

    .. note::
        Default headers: {'Accept': '\*/\*'}
    '''
    local = locals()
    if data is not None and isinstance(data, (basestring, dict)):
        return post(**local)
    return get(**local)



def fetch2(url, method="GET", data=None, headers={}, timeout=None, randua=True):
    ''' fetch url

    Args:
        url (str): url to fetch

    Kwargs:
        method (str): The request method, 'GET', 'POST', 'HEAD', 'PUT' OR 'DELETE'
                      
        data (dict/str):  The post data, it can be dict or string

        headers (dict):   The request headers

        timeout (double): The timeout

        randua (bool): Use random User-Agent when this is True

    Returns:
        response object

    .. note::
        Default headers: {'Accept': '\*/\*'}
    '''

    scheme, netloc, path, query, fragment = urlparse.urlsplit(url)
    method = method.upper()
    if method not in ("GET", "PUT", "DELETE", "POST", "HEAD"):
        method = "GET"

    requrl = path
    if query: requrl += '?' + query
    if fragment: requrl += '#' + fragment

    if '@' in netloc:
        auth, netloc = netloc.split('@', 1)
        auth = base64.b64encode(auth)
    else:
        auth = None
    
    if ':' in netloc:
        host, port = netloc.rsplit(':', 1)
        port = int(port)
    else:
        host, port = netloc, None
    
    if scheme == 'https':
        h = httplib.HTTPSConnection(host, port)
    elif scheme == 'http':
        h = httplib.HTTPConnection(host, port)
    else:
        raise Exception('Unsupported protocol %s' % scheme)
        
    if timeout is not None:
        h.connect()
        h.sock.settimeout(timeout)
    
    reqheaders = {
        'Accept' : '*/*',
        'User-Agent': fetch2.__globals__['randua']() if randua else 'urlfetch/' + __version__,
    }
    if auth: reqheaders['Authorization'] = 'Basic %s' % auth

    if isinstance(data, dict):
        data = urlencode(data)
    
    if isinstance(data, basestring) and method in ("POST", "PUT"):
        # httplib will set 'Content-Length', also you can set it by yourself
        reqheaders["Content-Type"] = "application/x-www-form-urlencoded"
        # what if the method is GET, HEAD or DELETE 
        # just do not make so much decisions for users

    for k, v in headers.iteritems():
        reqheaders[k.title()] = v 
    
    h.request(method, requrl, data, reqheaders)
    response = h.getresponse()
    setattr(response, 'reqheaders', reqheaders)
    setattr(response, 'body', response.read())
    h.close()
    
    return response

# some convient functions
get = partial(fetch2, method="GET")
post = partial(fetch2, method="POST")
put = partial(fetch2, method="PUT")
delete = partial(fetch2, method="DELETE")
head = partial(fetch2, method="HEAD")


if __name__ == '__main__':
    import sys
    url = sys.argv[1]
    
    response = fetch(url)
    print 'request headers', response.reqheaders
    print 'response headers', response.getheaders()
    print 'body length', len(response.body)
