import bottle
from bottle import request, response
import json
import hashlib

def md5sum(b):
    return hashlib.md5(b).hexdigest()

def mb_code(s, encoding='utf-8'):
    for c in ('utf-8', 'gb2312', 'gbk', 'gb18030', 'big5'):
        try:
            return s.decode(c).encode(encoding)
        except: pass
    try:
        return s.encode(encoding)
    except: raise 

def normal_formsdict():
    d = {}
    d['url'] = request.url
    d['path'] = request.path
    d['fullpath'] = request.fullpath
    d['method'] = request.method
    d['query_string'] = request.query_string
    d['script_name'] = request.script_name
    d['is_xhr'] = request.is_xhr
    d['is_ajax'] = request.is_ajax
    d['auth'] = request.auth
    d['remote_addr'] = request.remote_addr
    #d['environ'] = dict(request.environ)
    d['headers'] = dict(request.headers)

    #d['query'] = dict(request.query)
    d['forms'] = dict(request.forms)
    d['params'] = dict(request.params)
    d['get'] = dict(request.GET)
    d['post'] = dict(request.POST)
    d['files'] = dict(request.files)
    for i in d['files']:
        del d['post'][i]
        d['files'][i] = (d['files'][i].name, d['files'][i].filename, md5sum(d['files'][i].value))
    d['cookies'] = dict(request.cookies)
    return json.dumps(d)

app = bottle.app()

@app.route('/', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def index():
    return normal_formsdict()
    

def basic_auth_check(username, password):
    if username == "urlfetch" and password == "fetchurl":
        return True
    return False

@app.route('/basic_auth', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
@bottle.auth_basic(basic_auth_check)
def basic_auth():
    return normal_formsdict()

@app.route('/sleep/<seconds:int>', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def sleep(seconds):
    import time
    time.sleep(seconds)

    return normal_formsdict()

@app.route('/setcookie/<name>/<value>', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def setcookie(name, value):
    response.set_cookie(name, value)
    return normal_formsdict()


@app.route('http://www.example.com', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def index():
    return normal_formsdict()


import sys
try:
    port = int(sys.argv[1])
except:
    port = 8800

quiet = False
for arg in sys.argv[1:]:
    if arg == 'quiet':
        quiet = True
        break

bottle.debug(not quiet)
bottle.run(app=app, host='127.0.0.1', port=port, reloader=True, quiet=quiet, debug=not quiet,)
