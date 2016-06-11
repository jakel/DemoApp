from sqlalchemy import select, update
from sqlalchemy.sql import text
from DemoApp import app
from DemoApp.database import engine, metadata, ships, fleet_ships
from DemoApp.users import _get_user, _set_user_balance, _set_user_level, MAX_USER_LEVEL
from DemoApp.fleets import _get_fleet_by_num
from DemoApp.forms import BuildShipsForm, IShipForm
from DemoApp.utils import row2dict

from flask import session, redirect, url_for, request, render_template, flash
from datetime import datetime, timedelta

'''
ships = Table('ships', metadata,
    Column('ship_id', Integer, Sequence('ship_id_seq'), primary_key=True),
    Column('class', String(40)),
    Column('power', Integer),
    Column('min_lvl', Integer),
    Column('cost', Integer)
)

fleet_ships = Table('fleet_ships', metadata,
    Column('fs_id', Integer, Sequence('fs_id_seq'), primary_key=True),
    Column('ship_type', String(40), ForeignKey('ships.type'), nullable=False),
    Column('fleet_id', Integer, ForeignKey('fleets.fleet_id'), nullable=False),
    Column('number', Integer),
    Column('status', Enum('ACTIVE', 'BUILDING', 'DESTROYED')),
    Column('not_before', DateTime)
)
'''

POWER_LEVEL_DAMPENER = 2000

@app.before_request
def calulate_completed_ships():
    #s = text("UPDATE fleet_ships SET fleet_ships.status = \"ACTIVE\", fleet_ships.not_before = NULL
    #WHERE fleet_ships.status = \"BUILDING\" and fleet_ships.not_before <= date('now') ")
    s = fleet_ships.update().values({fleet_ships.c.status: 'ACTIVE', fleet_ships.c.not_before: None}) \
        .where(fleet_ships.c.status == 'BUILDING').where(fleet_ships.c.not_before <= datetime.now())
    conn = engine.connect()
    result = conn.execute(s)
    #print('Rows affected by update:', result.rowcount)
    result.close()
    return None

@app.before_request
def calulate_level():
    if 'user' not in session:
        return None
    user = _get_user()
    print(user)
    s = text("SELECT fs.ship_type, s.power as power, SUM(fs.number) as number from fleet_ships fs, ships s, fleets f \
    WHERE fs.ship_type = s.type and fs.fleet_id = f.fleet_id and f.user_id = %d and fs.status = \"ACTIVE\" \
    group by fs.ship_type" % (user['user_id']))
    conn = engine.connect()
    result = conn.execute(s)
    total_power = 0
    for row in result:
        if row['power'] is not None:
            total_power = total_power + (row['power'] * row['number'])
    if total_power == 0:
        return None
    new_lvl = MAX_USER_LEVEL * (total_power / float(total_power + POWER_LEVEL_DAMPENER))

    if new_lvl != user['lvl']:
        _set_user_level(conn, user['user_id'], new_lvl)
    return None

@app.route('/fleets/<int:num>/shipyard', methods = ['GET', 'POST'])
def build_ships(num):
    if 'user' not in session:
        redirect(url_for('login'))

    user = _get_user()
    fleet = _get_fleet_by_num(user['user_id'], num)
    #form = BuildShipsForm(request.form)
    ships_list = _load_ship_select_list()
    #print(ships_list)
    if request.method == 'POST':
        quantities = request.form.getlist('ships')
        data = []
        new_balance = user['balance']
        for i, q in enumerate(quantities):
            if q == '':
                continue
            try:
                quantity = int(q)
            except ValueError:
                flash('Invalid Quantity', 'danger')
                return redirect(url_for('fleet_index'))

            if quantity <= 0:
                continue
            if user['lvl'] >= ships_list[i]['min_lvl'] and new_balance >= ships_list[i]['cost'] * quantity:
                data.append({'ship_type': ships_list[i]['type'], 'fleet_id': fleet['fleet_id'], 'number': quantity,
                'status': 'BUILDING', 'not_before': datetime.now() + timedelta(seconds=ships_list[i]['build_speed']*quantity)})
                new_balance = new_balance - ships_list[i]['cost'] * quantity
            else:
                flash("Not enough money to buy %s %s's" % (quantity, ships_list[i]['type']), 'danger')
                return redirect(url_for('fleet_index'))
        if len(data) > 0:
            with engine.begin() as connection:
                connection.execute(fleet_ships.insert(), data)
                _set_user_balance(connection, user['user_id'], new_balance)
            flash('Way to build up your fleet!', 'success')

        return redirect(url_for('fleet_index'))
    return render_template('build_ships.html', fleet=fleet, ship_list=ships_list)


def _load_ship_select_list():
    ret = []
    s = select([ships]).distinct()
    #s = text("SELECT DISTINCT ships.type, ships.power, ships.min_lvl, ships.cost, ships.ship_id "
    #    "FROM ships"
    #    )
    conn = engine.connect()
    result = conn.execute(s)
    for row in result:
        ret.append(row2dict(row))
    return ret

def _load_ships_for_fleet(fleet_id):
    completed = []
    in_progress = []
    #sc = select([fleet_ships]).where(fleet_ships.c.fleet_id == fleet_id).where
    sc = text("SELECT fs.ship_type, s.power as power, SUM(fs.number) as number from fleet_ships fs, ships s \
    WHERE fs.ship_type = s.type and fs.fleet_id = %d and fs.status = \"ACTIVE\" group by fs.ship_type \
    order by s.power" % (fleet_id))
    conn = engine.connect()
    result = conn.execute(sc)
    for row in result:
        if 'ship_type' in row and row['ship_type'] is not None:
            completed.append(row2dict(row))

    si = select([fleet_ships]).where(fleet_ships.c.fleet_id == fleet_id).where(fleet_ships.c.status == "BUILDING")
    result = conn.execute(si)
    for row in result:
        in_progress.append(row2dict(row))
    return completed, in_progress
