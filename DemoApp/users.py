#from sqlalchemy import Table, Column, Integer, String, ForeignKey, Sequence, select
from sqlalchemy import select, update
from DemoApp import app
from DemoApp.database import engine, metadata, users
from flask import session, redirect, url_for, request, render_template
from DemoApp.forms import RegistrationForm, LoginForm
import string
import random
import hashlib
from datetime import timedelta
from datetime import datetime

'''
users = Table('users', metadata,
   Column('id', Integer, Sequence('user_id_seq'), primary_key=True),
   Column('username', String(50)),
   Column('fullname', String(50)),
   Column('password', String(65)),
   Column('salt', String(12)),
   Column('lvl', Integer),
   Column('balance', Integer),
   Column('last_calculated', DateTime)
)
'''

BALANCE_INC_PER_MINUTE = 10

@app.before_request
def calulate_balance():
    if 'user' in session and 'balance' in session['user']:
        conn = engine.connect()
        s = select([users]).where(users.c.username == session['user']['username'])
        result = conn.execute(s).fetchone()
        if result is None:
            session.pop('user', None)
            return redirect(url_for('register'))
        #print(result['balance'], session['user']['balance'])
        num_sec = (datetime.now() - result['last_calculated']).seconds
        num_min = int(num_sec / 60)
        if num_min < 1:
            if result['balance'] != session['user']['balance']:
                new_session = session['user']
                new_session['balance'] = result['balance']
                session['user'] = new_session
            return None
        remainder = num_sec % 60
        #print(result['balance'], num_min, remainder)
        u = users.update() \
                           .values({users.c.balance: (result['balance'] + (num_min * BALANCE_INC_PER_MINUTE)),
                            users.c.last_calculated: datetime.now() - timedelta(seconds=remainder)}) \
                            .where(users.c.id == result['id'])

        conn.execute(u)
        #print(session['user'])
        new_session = session['user']
        new_session['balance'] = result['balance'] + (num_min * BALANCE_INC_PER_MINUTE)
        #print(new_session)
        session['user'] = new_session
    return None

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():

        conn = engine.connect()
        s = select([users]).where(users.c.username == form.username.data)
        result = conn.execute(s).fetchone()
        if result is None:
            return render_template('login.html', form=form, error="Invalid Username Or Password")
        h = hashlib.sha256(result['salt'] + form.password.data).hexdigest()
        if result['password'] == h:
            session['user'] = {'username': result['username'], 'fullname': result['fullname'],
                'lvl': result['lvl'], 'balance': result['balance'], 'id': result['id']}
            return redirect(url_for('index'))
        #result.close()
        return render_template('login.html', form=form, error="Invalid Username Or Password")
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(12))
        h = hashlib.sha256(salt + form.password.data).hexdigest()
        print(salt, h)
        ins = users.insert().values(username=form.username.data, fullname=form.fullname.data,
            password=h, salt=salt, lvl=1, balance=5000, last_calculated=datetime.now())
        conn = engine.connect()
        result = conn.execute(ins)
        #Need to catch errors
        result.close()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


def _get_user():
    conn = engine.connect()
    s = select([users]).where(users.c.id == session['user']['id'])
    result = conn.execute(s).fetchone()
    return result

def _set_user_balance(conn, user_id=None, balance=None):
    conn.execute(users.update().where(users.c.id == user_id), balance=balance)
    new_session = session['user']
    new_session['balance'] = balance
    session['user'] = new_session
