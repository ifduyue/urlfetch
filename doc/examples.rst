Examples
=========

urlfetch at a glance
~~~~~~~~~~~~~~~~~~~~~

>>> import urlfetch
>>> r = urlfetch.get('https://twitter.com/')
>>> r.status, r.reason
(200, 'OK')
>>> r.total_time
0.924283027648926
>>> r.reqheaders
{'Host': 'twitter.com', 'Accept-Encoding': 'gzip, deflate, compress, identity, *
', 'Accept': '*/*', 'User-Agent': 'urlfetch/0.5.3'}
>>> len(r.content), type(r.content)
(72560, <type 'str'>)
>>> len(r.text), type(r.text)
(71770, <type 'unicode'>)
>>> r.headers
{'status': '200 OK', 'content-length': '15017', 'strict-transport-security': 'ma
x-age=631138519', 'x-transaction': '4a281c79631ee04e', 'content-encoding': 'gzip
', 'set-cookie': 'k=10.36.121.114.1359712350849032; path=/; expires=Fri, 08-Feb-
13 09:52:30 GMT; domain=.twitter.com, guest_id=v1%3A135971235085257249; domain=.
twitter.com; path=/; expires=Sun, 01-Feb-2015 21:52:30 GMT, _twitter_sess=BAh7Cj
oPY3JlYXRlZF9hdGwrCIXyK5U8AToMY3NyZl9pZCIlNGIwYjA2NWQ2%250AZGE0MGUzN2Y5Y2Y3NzViY
Tc5MjdkM2Q6FWluX25ld191c2VyX2Zsb3cwIgpm%250AbGFzaElDOidBY3Rpb25Db250cm9sbGVyOjpG
bGFzaDo6Rmxhc2hIYXNoewAG%250AOgpAdXNlZHsAOgdpZCIlM2Y4MDllNjVlNzA2M2Q0YTI4NjVmY2U
yMWYzZmRh%250AMWY%253D--2869053b52dc7269a8a09ee3608737e0291e4ec1; domain=.twitte
r.com; path=/; HttpOnly', 'expires': 'Tue, 31 Mar 1981 05:00:00 GMT', 'x-mid': '
eb2ca7a2ae1109f1b2aea10729cdcfd1d4821af5', 'server': 'tfe', 'last-modified': 'Fr
i, 01 Feb 2013 09:52:30 GMT', 'x-runtime': '0.13026', 'etag': '"15f3eb25198930fe
b6817975576b651b"', 'pragma': 'no-cache', 'cache-control': 'no-cache, no-store,
must-revalidate, pre-check=0, post-check=0', 'date': 'Fri, 01 Feb 2013 09:52:30
GMT', 'x-frame-options': 'SAMEORIGIN', 'content-type': 'text/html; charset=utf-8
', 'x-xss-protection': '1; mode=block', 'vary': 'Accept-Encoding'}
>>> r.getheaders()
[('status', '200 OK'), ('content-length', '15017'), ('expires', 'Tue, 31 Mar 198
1 05:00:00 GMT'), ('x-transaction', '4a281c79631ee04e'), ('content-encoding', 'g
zip'), ('set-cookie', 'k=10.36.121.114.1359712350849032; path=/; expires=Fri, 08
-Feb-13 09:52:30 GMT; domain=.twitter.com, guest_id=v1%3A135971235085257249; dom
ain=.twitter.com; path=/; expires=Sun, 01-Feb-2015 21:52:30 GMT, _twitter_sess=B
Ah7CjoPY3JlYXRlZF9hdGwrCIXyK5U8AToMY3NyZl9pZCIlNGIwYjA2NWQ2%250AZGE0MGUzN2Y5Y2Y3
NzViYTc5MjdkM2Q6FWluX25ld191c2VyX2Zsb3cwIgpm%250AbGFzaElDOidBY3Rpb25Db250cm9sbGV
yOjpGbGFzaDo6Rmxhc2hIYXNoewAG%250AOgpAdXNlZHsAOgdpZCIlM2Y4MDllNjVlNzA2M2Q0YTI4Nj
VmY2UyMWYzZmRh%250AMWY%253D--2869053b52dc7269a8a09ee3608737e0291e4ec1; domain=.t
witter.com; path=/; HttpOnly'), ('strict-transport-security', 'max-age=631138519
'), ('x-mid', 'eb2ca7a2ae1109f1b2aea10729cdcfd1d4821af5'), ('server', 'tfe'), ('
last-modified', 'Fri, 01 Feb 2013 09:52:30 GMT'), ('x-runtime', '0.13026'), ('et
ag', '"15f3eb25198930feb6817975576b651b"'), ('pragma', 'no-cache'), ('cache-cont
rol', 'no-cache, no-store, must-revalidate, pre-check=0, post-check=0'), ('date'
, 'Fri, 01 Feb 2013 09:52:30 GMT'), ('x-frame-options', 'SAMEORIGIN'), ('content
-type', 'text/html; charset=utf-8'), ('x-xss-protection', '1; mode=block'), ('va
ry', 'Accept-Encoding')]
>>> # getheader doesn't care whether you write 'content-length' or 'Content-Leng
th'
>>> # It's case insensitive
>>> r.getheader('content-length')
'15017'
>>> r.getheader('Content-Length')
'15017'
>>> r.cookies
{'guest_id': 'v1%3A135971235085257249', '_twitter_sess': 'BAh7CjoPY3JlYXRlZF9hdG
wrCIXyK5U8AToMY3NyZl9pZCIlNGIwYjA2NWQ2%250AZGE0MGUzN2Y5Y2Y3NzViYTc5MjdkM2Q6FWluX
25ld191c2VyX2Zsb3cwIgpm%250AbGFzaElDOidBY3Rpb25Db250cm9sbGVyOjpGbGFzaDo6Rmxhc2hI
YXNoewAG%250AOgpAdXNlZHsAOgdpZCIlM2Y4MDllNjVlNzA2M2Q0YTI4NjVmY2UyMWYzZmRh%250AMW
Y%253D--2869053b52dc7269a8a09ee3608737e0291e4ec1', 'k': '10.36.121.114.135971235
0849032'}
>>> r.cookiestring
'guest_id=v1%3A135971235085257249; _twitter_sess=BAh7CjoPY3JlYXRlZF9hdGwrCIXyK5U
8AToMY3NyZl9pZCIlNGIwYjA2NWQ2%250AZGE0MGUzN2Y5Y2Y3NzViYTc5MjdkM2Q6FWluX25ld191c2
VyX2Zsb3cwIgpm%250AbGFzaElDOidBY3Rpb25Db250cm9sbGVyOjpGbGFzaDo6Rmxhc2hIYXNoewAG%
250AOgpAdXNlZHsAOgdpZCIlM2Y4MDllNjVlNzA2M2Q0YTI4NjVmY2UyMWYzZmRh%250AMWY%253D--2
869053b52dc7269a8a09ee3608737e0291e4ec1; k=10.36.121.114.1359712350849032'

urlfetch.fetch
~~~~~~~~~~~~~~~~~

:func:`urlfetch.fetch` will determine the HTTP method (GET or POST) for you.

>>> import urlfetch
>>> # It's HTTP GET
>>> r = urlfetch.fetch("http://python.org/")
>>> r.status
200
>>> # Now it's HTTP POST
>>> r = urlfetch.fetch("http://python.org/", data="foobar")
>>> r.status
200

Add HTTP headers
~~~~~~~~~~~~~~~~~~~

>>> from urlfetch import fetch
>>> r = fetch("http://python.org/", headers={"User-Agent": "urlfetch"})
>>> r.status
200
>>> r.reqheaders
{'Host': u'python.org', 'Accept': '*/*', 'User-Agent': 'urlfetch'}
>>> # alternatively, you can turn randua on 
>>> # ranua means generate a random user-agent
>>> r = fetch("http://python.org/", randua=True)
>>> r.status
200
>>> r.reqheaders
{'Host': u'python.org', 'Accept': '*/*', 'User-Agent': 'Mozilla/5.0 (Windows NT
6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.8 Safari/535.1
'}
>>> r = fetch("http://python.org/", randua=True)
>>> r.status
200
>>> r.reqheaders
{'Host': u'python.org', 'Accept': '*/*', 'User-Agent': 'Mozilla/5.0 (Windows; U;
 Windows NT 6.0; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6 (.NET CLR 3.5.30729
)'}


POST data
~~~~~~~~~~~

>>> from urlfetch import post
>>> r = post("http://python.org", data={'foo': 'bar'})
>>> r.status
200
>>> # data can be bytes
>>> r = post("http://python.org", data="foo=bar")
>>> r.status
200


Upload files
~~~~~~~~~~~~~~

>>> from urlfetch import post
>>> r = post(
...         'http://127.0.0.1:8888/',
...         headers = {'Referer': 'http://127.0.0.1:8888/'},
...         data = {'foo': 'bar'},
...         files = {
...             'formname1': open('/tmp/path/to/file1', 'rb'),
...             'formname2': ('filename2', open('/tmp/path/to/file2', 'rb')),
...             'formname3': ('filename3', 'binary data of /tmp/path/to/file3'),
...         },
...     )
>>> r.status
200

Basic auth and call github API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

>>> from urlfetch import get
>>> import pprint
>>> r = get('https://api.github.com/gists', auth=('username', 'password'))
>>> pprint.pprint(r.json)
[{u'comments': 0,
  u'created_at': u'2012-03-21T15:22:13Z',
  u'description': u'2_urlfetch.py',
  u'files': {u'2_urlfetch.py': {u'filename': u'2_urlfetch.py',
                               	u'language': u'Python',
                               	u'raw_url': u'https://gist.github.com/raw/2148359/58c9062e0fc7bf6b9c43d2cf345ec4e6df2fef3e/2_urlfetch.py',
                               	u'size': 218,
                               	u'type': u'application/python'}},
  u'git_pull_url': u'git://gist.github.com/2148359.git',
  u'git_push_url': u'git@gist.github.com:2148359.git',
  u'html_url': u'https://gist.github.com/2148359',
  u'id': u'2148359',
  u'public': True,
  u'updated_at': u'2012-03-21T15:22:13Z',
  u'url': u'https://api.github.com/gists/2148359',
  u'user': {u'avatar_url': u'https://secure.gravatar.com/avatar/68b703a082b87cce010b1af5836711b3?d=https://a248.e.akamai.net/assets.github.com%2Fimages%2Fgrava
tars%2Fgravatar-140.png',
            u'gravatar_id': u'68b703a082b87cce010b1af5836711b3',
            u'id': 568900,
            u'login': u'ifduyue',
            u'url': u'https://api.github.com/users/ifduyue'}},
 ...]
 
 
 
:class:`urlfetch.Session`
~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`urlfetch.Session` can hold common headers and cookies.
Every request issued by a :class:`urlfetch.Session` object will bring up
these headers and cookies.
:class:`urlfetch.Session` plays a role in handling cookies, just like a
cookiejar.

>>> from urlfetch import Session
>>> s = Session(headers={"User-Agent": "urlfetch session"}, cookies={"foo": "bar"})
>>> r = s.get("https://twitter.com/")
>>> r.status
200
>>> r.reqheaders
{'Host': u'twitter.com', 'Cookie': 'foo=bar', 'Accept': '*/*', 'User-Agent': 'ur
lfetch session'}
>>> r.cookies
{'guest_id': 'v1%3A134136902538582791', '_twitter_sess': 'BAh7CDoPY3JlYXRlZF9hdG
wrCGoD0084ASIKZmxhc2hJQzonQWN0aW9uQ29u%250AdHJvbGxlcjo6Rmxhc2g6OkZsYXNoSGFzaHsAB
joKQHVzZWR7ADoHaWQiJWM2%250AMDAyMTY2YjFhY2YzNjk3NzU3ZmEwYTZjMTc2ZWI0--81b8c092d2
64be1adb8b52eef177ab4466520f65', 'k': '10.35.53.118.1341369025382790'}
>>> r.cookiestring
'guest_id=v1%3A134136902538582791; _twitter_sess=BAh7CDoPY3JlYXRlZF9hdGwrCGoD008
4ASIKZmxhc2hJQzonQWN0aW9uQ29u%250AdHJvbGxlcjo6Rmxhc2g6OkZsYXNoSGFzaHsABjoKQHVzZW
R7ADoHaWQiJWM2%250AMDAyMTY2YjFhY2YzNjk3NzU3ZmEwYTZjMTc2ZWI0--81b8c092d264be1adb8
b52eef177ab4466520f65; k=10.35.53.118.1341369025382790'
>>> s.putheader("what", "a nice day")
>>> s.putcookie("yah", "let's dance")
>>> r = s.get("https://twitter.com/")
>>> r.status
200
>>> r.reqheaders
{'Host': u'twitter.com', 'Cookie': "guest_id=v1%3A134136902538582791; _twitter_s
ess=BAh7CDoPY3JlYXRlZF9hdGwrCGoD0084ASIKZmxhc2hJQzonQWN0aW9uQ29u%250AdHJvbGxlcjo
6Rmxhc2g6OkZsYXNoSGFzaHsABjoKQHVzZWR7ADoHaWQiJWM2%250AMDAyMTY2YjFhY2YzNjk3NzU3Zm
EwYTZjMTc2ZWI0--81b8c092d264be1adb8b52eef177ab4466520f65; k=10.35.53.118.1341369
025382790; foo=bar; yah=let's dance", 'What': 'a nice day', 'Accept': '*/*', 'Us
er-Agent': 'urlfetch session'}


Streaming
~~~~~~~~~~~~

>>> import urlfetch
>>> with urlfetch.get('http://some.very.large/file') as r:
>>>     with open('some.very.large.file', 'wb') as f:
>>>         for chunk in r:
>>>             f.write(chunk)


Proxies
~~~~~~~~~~~~

>>> from urlfetch import get
>>> r = get('http://docs.python.org/', proxies={'http':'127.0.0.1:8888'})
>>> r.status, r.reason
(200, 'OK')
>>> r.headers
{'content-length': '8719', 'via': '1.1 tinyproxy (tinyproxy/1.8.2)', 'accept-ran
ges': 'bytes', 'vary': 'Accept-Encoding', 'server': 'Apache/2.2.16 (Debian)', 'l
ast-modified': 'Mon, 30 Jul 2012 19:22:48 GMT', 'etag': '"13cc5e4-220f-4c610fcaf
d200"', 'date': 'Tue, 31 Jul 2012 04:18:26 GMT', 'content-type': 'text/html'}

Redirects
~~~~~~~~~~~~~~

>>> from urlfetch import get
>>> r = get('http://tinyurl.com/urlfetch', max_redirects=10)
>>> r.history
[<urlfetch.Response object at 0x274b8d0>]
>>> r.history[-1].headers
{'content-length': '0', 'set-cookie': 'tinyUUID=036051f7dc296a033f0608cf; expire
s=Fri, 23-Aug-2013 10:25:30 GMT; path=/; domain=.tinyurl.com', 'x-tiny': 'cache
0.0016100406646729', 'server': 'TinyURL/1.6', 'connection': 'close', 'location':
 'https://github.com/ifduyue/urlfetch', 'date': 'Thu, 23 Aug 2012 10:25:30 GMT',
'content-type': 'text/html'}
>>> r.headers
{'status': '200 OK', 'content-encoding': 'gzip', 'transfer-encoding': 'chunked',
 'set-cookie': '_gh_sess=BAh7BzoPc2Vzc2lvbl9pZCIlN2VjNWM3NjMzOTJhY2YyMGYyNTJlYzU
4NmZjMmRlY2U6EF9jc3JmX3Rva2VuIjFlclVzYnpxYlhUTlNLV0ZqeXg4S1NRQUx3VllmM3VEa2ZaZml
iRHBrSGRzPQ%3D%3D--cbe63e27e8e6bf07edf0447772cf512d2fbdf2e2; path=/; expires=Sat
, 01-Jan-2022 00:00:00 GMT; secure; HttpOnly', 'strict-transport-security': 'max
-age=2592000', 'connection': 'keep-alive', 'server': 'nginx/1.0.13', 'x-runtime'
: '104', 'etag': '"4137339e0195583b4f034c33202df9e8"', 'cache-control': 'private
, max-age=0, must-revalidate', 'date': 'Thu, 23 Aug 2012 10:25:31 GMT', 'x-frame
-options': 'deny', 'content-type': 'text/html; charset=utf-8'}
>>>
>>> # If max_redirects exceeded, an exeception will be raised
>>> r = get('http://google.com/', max_redirects=1)
Traceback (most recent call last):
  File "<input>", line 1, in <module>
  File "urlfetch.py", line 627, in request
    raise UrlfetchException('max_redirects exceeded')
UrlfetchException: max_redirects exceeded
