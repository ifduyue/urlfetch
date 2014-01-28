#!/usr/bin/env python
#
#   Example of usage pool with gevent
#

from gevent import monkey
monkey.patch_socket()

from gevent.pool import Pool
import urlfetch

pool = Pool(size=5)
urls = ('http://www.google.com', 'http://www.yahoo.com',
        'http://www.blogger.com', 'http://www.python.org',
        'http://sourceforge.net', 'http://www.ubuntu.com',
        'http://www.readwriteweb.com', 'http://gigaom.com',
        'http://www.wired.com')

tasks = pool.map(urlfetch.get, urls)

