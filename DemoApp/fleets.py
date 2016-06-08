from sqlalchemy import select, update
from DemoApp import app
from DemoApp.database import engine, metadata, fleets
from DemoApp.users import _get_user, _set_user_balance
#from DemoApp.forms import NewFleetForm
from flask import session, redirect, url_for, request, render_template
#from DemoApp.forms import RegistrationForm, LoginForm
from datetime import datetime, timedelta

'''
fleets = Table('fleets', metadata,
    Column('fleet_id', Integer, Sequence('fleet_id_seq'), primary_key=True),
    Column('user_id', None, ForeignKey('users.id')),
    Column('status', Enum('ACTIVE', 'IN_TRANSIT', 'DESTROYED')),
    Column('fleet_num', Integer),
    Column('island_id', Integer),
    Column('island_not_before', DateTime)
)
'''

FLEET_BASE_COST = 5000
MAX_FLEET_NUM = 10

@app.route('/fleets')
def fleet_index():
    if 'user' not in session:
        redirect(url_for('login'))
    print(session['user'])
    f = _get_fleets(session['user']['id'])
    print(f)
    return render_template('fleets.html', fleets=f)


@app.route('/fleets/new')
def new_fleet():
    if 'user' not in session:
        redirect(url_for('login'))
    user = _get_user()
    f = _get_fleets(user['id'])
    if len(f) >= MAX_FLEET_NUM:
        return redirect(url_for('fleet_index')) # too many fleets
    fleet_cost = 2**len(f) * FLEET_BASE_COST
    print(fleet_cost)
    if fleet_cost > user['balance']:
        return redirect(url_for('fleet_index'))

    with engine.begin() as connection:
        connection.execute(fleets.insert(), user_id=user['id'], status='ACTIVE',
        fleet_num= _get_lowest_fleet_num(f))
        _set_user_balance(connection, user['id'], user['balance'] - fleet_cost)
    #ins = fleets.insert().values(user_id=user['id'], status='ACTIVE',
    #fleet_num= _get_lowest_fleet_num(f))
    #conn.execute(ins)

    return redirect(url_for('fleet_index'))


'''
 Next ship cost is equal to
 2^(num_fleets) * FLEET_BASE_COST
'''

def _get_fleets(user_id=None):
    ret = []
    s = select([fleets]).where(fleets.c.user_id == user_id)
    conn = engine.connect()
    result = conn.execute(s)
    for row in result:
        ret.append({'fleet_id': row['fleet_id'], 'user_id': row['user_id'],
        'status': row['status'], 'fleet_num': row['fleet_num']})
    return ret

def _get_lowest_fleet_num(fleets=[]):
    for x in range(MAX_FLEET_NUM):
        ret = x + 1
        is_in = False
        for fleet in fleets:
            if fleet['fleet_num'] == ret:
                is_in = True
        if not is_in:
            return ret
    return 0 # return bad fleet num
