Examples
=========

urlfetch at a glance
~~~~~~~~~~~~~~~~~~~~~

>>> import urlfetch
>>> r = urlfetch.get("http://python.org/")
>>> r.status, r.reason
(200, 'OK')
>>> r.reqheaders
{'Host': u'python.org', 'Accept': '*/*', 'User-Agent': 'urlfetch/0.4.0'}
>>> len(r.content), type(r.content)
(19020, <type 'str'>)
>>> len(r.text), type(r.text)
(19016, <type 'unicode'>)
>>> r.headers
{'content-length': '19020', 'x-cache': 'HIT from localhost', 'x-cache-lookup': '
HIT from localhost:8080', 'vary': 'Accept-Encoding', 'server': 'Apache/2.2.16 (D
ebian)', 'last-modified': 'Tue, 03 Jul 2012 10:48:45 GMT', 'connection': 'close'
, 'etag': '"105800d-4a4c-4c3eaa895dd40"', 'date': 'Wed, 04 Jul 2012 01:32:15 GMT
', 'age': '179', 'content-type': 'text/html', 'accept-ranges': 'bytes'}
>>> r.getheaders()
[('content-length', '19020'), ('x-cache', 'HIT from localhost'), ('accept-ranges
', 'bytes'), ('vary', 'Accept-Encoding'), ('server', 'Apache/2.2.16 (Debian)'),
('x-cache-lookup', 'HIT from localhost:8080'), ('last-modified', 'Tue, 03 Jul 20
12 10:48:45 GMT'), ('connection', 'close'), ('etag', '"105800d-4a4c-4c3eaa895dd4
0"'), ('date', 'Wed, 04 Jul 2012 01:32:15 GMT'), ('content-type', 'text/html'),
('age', '179')]
>>> # getheader doesn't care whether you write 'content-length' or 'Content-Length'
>>> # It's case insensitive
>>> r.getheader('content-length')
'19020'
>>> r.getheader('Content-Length')
'19020'
>>> r.cookies
{}
>>> r.cookiestring
''

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
            u'login': u'lyxint',
            u'url': u'https://api.github.com/users/lyxint'}},
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
>>> s.dumps(cls="json")
'{"headers": {"What": "a nice day", "User-Agent": "urlfetch session"}, "cookies"
: {"guest_id": "v1%3A134136902538582791", "_twitter_sess": "BAh7CDoPY3JlYXRlZF9h
dGwrCGoD0084ASIKZmxhc2hJQzonQWN0aW9uQ29u%250AdHJvbGxlcjo6Rmxhc2g6OkZsYXNoSGFzaHs
ABjoKQHVzZWR7ADoHaWQiJWM2%250AMDAyMTY2YjFhY2YzNjk3NzU3ZmEwYTZjMTc2ZWI0--81b8c092
d264be1adb8b52eef177ab4466520f65", "k": "10.35.53.118.1341369025382790", "foo":
"bar", "yah": "let\'s dance"}}'
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


