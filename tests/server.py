import os
import json
import hashlib
import bottle
from bottle import request, response, static_file, abort

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
        d['files'][i] = (d['files'][i].name, d['files'][i].filename, md5sum(d['files'][i].file.read()))
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
def proxy():
    return normal_formsdict()

@app.route('/utf8.txt')
def utf8_file():
    return static_file('test.file', root=os.path.dirname(__file__))

@app.route('/gbk.txt')
def gbk_file():
    return static_file('test.file.gbk', root=os.path.dirname(__file__))

@app.route('/redirect/<max>/<now>', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def redirect(max, now):
    max = int(max)
    now = int(now)
    if now == max:
        return normal_formsdict()
    elif now < max:
        return bottle.redirect('/redirect/%s/%s' % (max, now+1))
    else:
        abort(400)

@app.route('/content-encoding/invalid-header')
def content_encoding_invalid_header():
    response.set_header('Content-Encoding', 'invalid')
    return os.urandom(64)

@app.route('/content-encoding/invalid-body')
def content_encoding_invalid_body():
    response.set_header('Content-Encoding', 'gzip')
    return os.urandom(64)

@app.route('/content-encoding/invalid-body/deflate')
def content_encoding_invalid_body():
    response.set_header('Content-Encoding', 'deflate')
    return os.urandom(64)
    
@app.route('/links/<n>')
def links(n):
    try:
        n = int(n)
    except:
        n = None
    if n == 1:
        response.set_header('Link', '</links/2>; rel="next", </links/3>; rel="last"')
    elif n == 2:
        response.set_header('Link', '</links/3>; rel="next", </links/3>; rel="last", </links/1>; rel="prev", </links/1>; rel="first"')
    elif n == 3:
        response.set_header('Link', '</links/1>; rel="prev", </links/1>; rel="first"')
    elif n is None:
        response.set_header('Link', '</links/none>; rel="self"')
    else:
        response.set_header('Link', '</links/1>')
    return normal_formsdict()

@app.route('/bytes/<n:int>', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def sleep(n):
    return os.urandom(int(n))

def run():
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
    bottle.run(app=app, host='127.0.0.1', port=port, server='gunicorn',
               quiet=quiet, debug=not quiet,)

if __name__ == '__main__':
    run()
