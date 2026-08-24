import os
import json
import hashlib
import gzip
import zlib
from io import BytesIO
import bottle
from bottle import request, response, static_file, abort

COMPRESSION_PAYLOAD = b"urlfetch-compression-fixture"

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
    response.set_cookie(name, value, path='/')
    return normal_formsdict()

@app.route('/setcookies', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def setcookies():
    response.set_cookie('one', '1', path='/')
    response.set_cookie('two', '2', path='/')
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

@app.route('/redirect-status/<code:int>', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def redirect_status(code):
    response.status = int(code)
    response.set_header('Location', '/')
    return ''

@app.route('/redirect-cross-host', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS', 'PATCH'])
def redirect_cross_host():
    host = request.get_header('Host') or '127.0.0.1:8800'
    port = host.rsplit(':', 1)[-1] if ':' in host else '8800'
    if host.startswith('127.0.0.1'):
        target = 'http://localhost:%s/' % port
    else:
        target = 'http://127.0.0.1:%s/' % port
    return bottle.redirect(target)

@app.route('/content-encoding/invalid-header')
def content_encoding_invalid_header():
    response.set_header('Content-Encoding', 'invalid')
    return os.urandom(256)

@app.route('/content-encoding/invalid-body')
def content_encoding_invalid_body():
    response.set_header('Content-Encoding', 'gzip')
    return os.urandom(256)

@app.route('/content-encoding/invalid-body/deflate')
def content_encoding_invalid_body_deflate():
    response.set_header('Content-Encoding', 'deflate')
    return os.urandom(256)

@app.route('/content-encoding/gzip')
def content_encoding_gzip():
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb') as gz:
        gz.write(COMPRESSION_PAYLOAD)
    response.set_header('Content-Encoding', 'gzip')
    response.set_header('Content-Type', 'application/octet-stream')
    return buf.getvalue()

@app.route('/content-encoding/deflate')
def content_encoding_deflate():
    response.set_header('Content-Encoding', 'deflate')
    response.set_header('Content-Type', 'application/octet-stream')
    return zlib.compress(COMPRESSION_PAYLOAD)
    
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

@app.route('/status/<code:int>')
def status_code(code):
    abort(int(code), 'error')

@app.route('/echo-body', method=['POST', 'PUT', 'PATCH'])
def echo_body():
    body = request.body.read()
    if isinstance(body, bytes):
        body = body.decode('utf-8', 'replace')
    return json.dumps({
        'method': request.method,
        'content_type': request.content_type,
        'body': body,
    })

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
