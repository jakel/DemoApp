from sqlalchemy import select, update
from DemoApp import app
from DemoApp.database import engine, metadata, fleets
from DemoApp.users import _get_user, _set_user_balance, _set_user_level, _get_username_by_id
from DemoApp.utils import row2dict

#from DemoApp.forms import NewFleetForm
from flask import session, redirect, url_for, request, render_template, flash
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
DESTROYED_FLEET_RETURN_PERCENTAGE = 60

@app.before_request
def update_traveling_fleets():
    #s = text("UPDATE fleet_ships SET fleet_ships.status = \"ACTIVE\", fleet_ships.not_before = NULL
    #WHERE fleet_ships.status = \"BUILDING\" and fleet_ships.not_before <= date('now') ")
    s = fleets.update().values({fleets.c.status: 'ACTIVE', fleets.c.island_not_before: None}) \
        .where(fleets.c.status == 'IN_TRANSIT').where(fleets.c.island_not_before <= datetime.now())
    conn = engine.connect()
    result = conn.execute(s)
    #print('Rows affected by update:', result.rowcount)
    result.close()
    return None

@app.route('/fleets')
def fleet_index():
    if 'user' not in session:
        redirect(url_for('login'))
    #print(session['user'])
    f = _get_fleets(session['user']['user_id'])
    #print(f)
    return render_template('fleets.html', fleets=f, next_fleet_cost= '{:,}R'.format(2**len(f) * FLEET_BASE_COST))

'''
 Next ship cost is equal to
 2^(num_fleets) * FLEET_BASE_COST
'''
@app.route('/fleets/new')
def new_fleet():
    if 'user' not in session:
        redirect(url_for('login'))
    user = _get_user()
    f = _get_fleets(user['user_id'])
    if len(f) >= MAX_FLEET_NUM:
        flash('You already have the max number of fleets!', 'danger')
        return redirect(url_for('fleet_index')) # too many fleets
    fleet_cost = 2**len(f) * FLEET_BASE_COST
    if fleet_cost > user['balance']:
        flash("You don't have enough Reales to create a new Fleet!", 'danger')
        return redirect(url_for('fleet_index'))

    with engine.begin() as connection:
        connection.execute(fleets.insert(), user_id=user['user_id'], status='ACTIVE',
        fleet_num= _get_lowest_fleet_num(f))
        _set_user_balance(connection, user['user_id'], user['balance'] - fleet_cost)

    flash('Congratulations! you created a new Fleet!', 'success')
    return redirect(url_for('fleet_index'))


@app.route('/fleets/<int:num>')
def fleet_info(num=1):
    if 'user' not in session:
        redirect(url_for('login'))
    user = _get_user()
    fleet = _get_fleet_by_num(user['user_id'], num)
    ships_completed, ships_in_progress = _load_ships_for_fleet(fleet['fleet_id'])
    print(fleet, ships_completed, ships_in_progress)
    return render_template('fleet_info.html', fleet=fleet, ships_completed=ships_completed, ships_in_progress=ships_in_progress)

@app.route('/fleets/<int:num>/combat', methods = ['GET', 'POST'])
def fleet_combat(num):
    if 'user' not in session:
        redirect(url_for('login'))

    target = request.args.get('target', None)
    if target is None:
        return redirect(url_for('fleet_index'))

    try:
        target = int(target)
    except ValueError:
        flash('Invalid Combat Target', 'danger')
        return redirect(url_for('fleet_index'))

    user = _get_user()
    fleet = _get_fleet_by_num(user['user_id'], num)
    fsc, fsp = _load_ships_for_fleet(fleet['fleet_id'])
    fleet['ships'] = {'completed': fsc, 'in_progress': fsp}

    target_fleet = _get_fleet_by_id(target)
    tfsc, tfsp = _load_ships_for_fleet(target_fleet['fleet_id'])
    target_fleet['ships'] = {'completed': tfsc, 'in_progress': tfsp}

    if request.method == 'POST':
        if fleet.island_not_before is not None or target_fleet.island_not_before is not None:
            flash('One Fleet in Transit. Both fleets must arrive before you can fight!', 'danger')
            return redirect(url_for('fleet_index'))

        pass

    return render_template('fleet_combat.html', fleet=fleet, target=target_fleet)

def _get_fleet_by_num(user_id, fleet_num):
    s = select([fleets]).where(fleets.c.user_id == user_id).where(fleets.c.fleet_num == fleet_num)
    conn = engine.connect()
    result = conn.execute(s).fetchone()
    fleet = row2dict(result)
    fleet['island_name'] =_get_island_name_by_id(fleet['island_id'])
    return fleet

def _get_fleet_by_id(fleet_id):
    s = select([fleets]).where(fleets.c.fleet_id == fleet_id)
    conn = engine.connect()
    result = conn.execute(s).fetchone()
    fleet = row2dict(result)
    fleet['island_name'] =_get_island_name_by_id(fleet['island_id'])
    return fleet


def _get_fleets(user_id=None):
    ret = []
    s = select([fleets]).where(fleets.c.user_id == user_id)
    conn = engine.connect()
    result = conn.execute(s)
    for row in result:
        fleet = row2dict(row)
        fleet['island_name'] =_get_island_name_by_id(fleet['island_id'])
        ret.append(fleet)
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

def _get_fleets_by_island(island_id):
    ret = []
    s = select([fleets]).where(fleets.c.island_id == island_id)
    conn = engine.connect()
    result = conn.execute(s)
    for row in result:
        fleet = row2dict(row)
        fleet['username'] = _get_username_by_id(fleet['user_id'])
        ret.append(fleet)
    return ret

def _set_fleet_location(fleet_id, island_id, island_not_before):
    u = fleets.update().values({"island_id": island_id, 'island_not_before': island_not_before, 'status': 'IN_TRANSIT'})\
    .where(fleets.c.fleet_id == fleet_id)
    conn = engine.connect()
    return conn.execute(u)


# SUPER HACKY... importing ships at the end because its a circular dep
from DemoApp.ships import _load_ships_for_fleet
from DemoApp.map import _get_island_name_by_id
