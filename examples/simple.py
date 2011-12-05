import urlfetch
import sys


url = sys.argv[1]
try:
    response = urlfetch.fetch(url)
    print response.body
except Exception, e:
    print 'error fetching %s: %s' % (url, e)

# try this in console:
# python simple.py https://github.com/
