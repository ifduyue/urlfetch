#!/usr/bin/env python
#-*- coding: utf-8 -*-
# http://pypi.python.org/pypi/urlfetch

import urlfetch

r = urlfetch.get('https://api.github.com', auth=('user', 'pass'))

print r.status
print r.getheader('content-type')
