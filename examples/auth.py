#!/usr/bin/env python
# http://pypi.python.org/pypi/urlfetch

import urlfetch

r = urlfetch.get('https://api.github.com', auth=('user', 'pass'))

print(r.status)
print(r.getheader('content-type'))
