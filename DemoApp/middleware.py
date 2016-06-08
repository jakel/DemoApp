#from flask import session, request
#from DemoApp.database import engine, users

class BalanceMiddleWare(object):
    """Simple WSGI middleware
    """
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        #print 'something you want done in every http request'

        return self.app(environ, start_response)
