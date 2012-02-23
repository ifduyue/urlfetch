import bottle
from bottle import request
import json

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
        d['files'][i] = (d['files'][i].name, d['files'][i].filename, d['files'][i].value)
    d['cookies'] = dict(request.cookies)
    return json.dumps(d)

app = bottle.app()

@app.route('/', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS'])
def index():
    return normal_formsdict()
    

def basic_auth_check(username, password):
    if username == "urlfetch" and password == "fetchurl":
        return True
    return False

@app.route('/basic_auth', method=['GET', 'POST', 'PUT', 'HEAD', 'DELETE', 'OPTIONS'])
@bottle.auth_basic(basic_auth_check)
def basic_auth():
    return normal_formsdict()


bottle.run(app=app, host='127.0.0.1', port=8800)
