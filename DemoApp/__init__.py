# Import flask and template operators
from flask import Flask
#from flask_mysqldb import MySQL

# Import SQLAlchemy
#from flask_sqlalchemy import SQLAlchemy
from DemoApp.database import init_db
import DemoApp.middleware
import os

app = Flask(__name__)

# Configurations
#app.config.from_object('config')
app.config['SESSION_COOKIE_NAME'] = 'PR_SESSION'
#app.config['SESSION_COOKIE_DOMAIN'] = 'PR_DOMAIN'
app.config['SESSION_REFRESH_EACH_REQUEST'] = True


#app.wsgi_app = middleware.BalanceMiddleWare(app.wsgi_app)

if 'PR_SECRET_KEY' in os.environ:
    app.secret_key = os.environ['PR_SECRET_KEY']
else:
    # set throwaway key for easy debugging
    app.secret_key = '\x91/\x0bu \x88W\rN\x01\xdb\x0f\x1dj\\\xe5\xa7\x94\xe0U\xa7b\x87e'


#import routes from controllers
from DemoApp.main import index
import DemoApp.users
import DemoApp.fleets
import DemoApp.ships
import DemoApp.map

def main(options, env='dev'):
    init_db(options.debug)

    # start the app
    app.run(host='0.0.0.0', debug=options.debug)
