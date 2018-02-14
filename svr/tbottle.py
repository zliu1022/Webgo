import time
from bottle import route, run, template, error, debug
from bottle import get, post, request # or route
import bottle

@route('/hello/<name>')
def index(name):
  time.sleep(5)
  try:
    return template('<b>Hello {{name}}</b>!', name=name)
  except Exception:
    print "error1"
  finally:
    print "finally"

def error_handler_500(error):
  return 'error_handler_500'

#default_app().error(code=500, callback=error_handler_500)

@error(404)
def error_handler_404(error):
  return 'error_handler_404'

@error(500)
def error_handler_500(error):
  print "500"
  return 'error_handler_404'

@error(10053)
def error_handler_10053(error):
  print "10053"
  return 'error_handler_404'

@get('/login') # or @route('/login')
def login():
    return '''
        <form action="/login" method="post">
            Username: <input name="username" type="text" />
            Password: <input name="password" type="password" />
            <input value="Login" type="submit" />
        </form>
    '''

@post('/login') # or @route('/login', method='POST')
def do_login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    if check_login(username, password):
        return "<p>Your login information was correct.</p>"
    else:
        return "<p>Login failed.</p>"

debug(True)
bottle.app().catchall=True
run(host='localhost', port=32001)

