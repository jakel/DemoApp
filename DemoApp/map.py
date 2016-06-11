from sqlalchemy import select, update, text
from DemoApp import app
from DemoApp.database import engine, metadata, map_table
from DemoApp.users import _get_user, _set_user_balance, _set_user_level
from DemoApp.utils import row2dict
from DemoApp.fleets import _get_fleets_by_island, _get_fleet_by_num, _set_fleet_location
from DemoApp.forms import MoveFleetForm

from flask import session, redirect, url_for, request, render_template, flash
from datetime import datetime, timedelta
from math import pow, sqrt

'''
map_table = Table('map', metadata,
    Column('map_id', Integer, Sequence('map_id_seq'), primary_key=True),
    Column('island_name', String(40)),
    Column('pos_x', Integer),
    Column('pos_y', Integer)
)
'''

DEFAULT_TRAVEL_DISTANCE = 100
TRAVEL_TIME_PER_DISTANCE = 5

@app.route('/map')
def render_map():
    if 'user' not in session:
        redirect(url_for('login'))

    x = request.args.get('x', None)
    y = request.args.get('y', None)
    if x is None and y is None:
        return render_template('map.html')

    # Select and add map locations
    s = select([map_table]).where(map_table.c.pos_x >= int(x) * 100) \
    .where(map_table.c.pos_x < (int(x)+1) * 100).where(map_table.c.pos_y >= int(y) * 100) \
    .where(map_table.c.pos_y < (int(y)+1) * 100)

    map_points = []
    conn = engine.connect()
    result = conn.execute(s)
    for row in result:
        map_points.append(row2dict(row))

    return render_template('map.html', x=int(x), y=int(y), map_points=map_points)


@app.route('/map/island/<name>')
def island_details(name):
    if 'user' not in session:
        redirect(url_for('login'))

    s = select([map_table]).where(map_table.c.island_name == name)
    conn = engine.connect()
    island = conn.execute(s).fetchone()
    if island is None:
        return redirect(url_for('render_map'))

    fleets = _get_fleets_by_island(island['map_id'])
    #print(fleets)
    return render_template('map_details.html', island=island, fleets=fleets)

@app.route('/fleets/<int:num>/move', methods = ['GET', 'POST'])
def move_fleet(num):
    if 'user' not in session:
        redirect(url_for('login'))
    user = _get_user()
    fleet = _get_fleet_by_num(user['user_id'], num)
    if fleet is None:
        return redirect(url_for('fleet_index'))

    stmt = text("SELECT map_id, island_name, pos_x, pos_y FROM map") \
        .columns(map_table.c.map_id, map_table.c.island_name, map_table.c.pos_x, map_table.c.pos_y)
    #stmt = stmt
    conn = engine.connect()
    islands = conn.execute(stmt).fetchall()

    if request.method == 'POST':
        print(request.form)
        if 'destination' in request.form:
            des_id = request.form['destination']
            try:
                des_id = int(des_id)
            except ValueError:
                flash('Invalid Destination', 'danger')
                return render_template('move_fleet.html', fleet=fleet, islands=islands)

            if des_id is None or _get_island_from_list(des_id, islands) is None:
                #bad request
                return render_template('move_fleet.html', fleet=fleet, islands=islands)
            current_island = _get_island_from_list(fleet['island_id'], islands)
            target_island = _get_island_from_list(des_id, islands)
            distance = _get_travel_distance(current_island, target_island)

            travel_time = datetime.now() + timedelta(seconds=distance * TRAVEL_TIME_PER_DISTANCE)
            _set_fleet_location(fleet['fleet_id'], target_island['map_id'], travel_time)
            return redirect(url_for('fleet_index'))

    return render_template('move_fleet.html', fleet=fleet, islands=islands)

def _get_travel_distance(current_island, target_island):
    if current_island is None:
        return DEFAULT_TRAVEL_DISTANCE
    distance = sqrt( pow(abs(target_island['pos_x'] - current_island['pos_x']) ,2) \
        + pow(abs(target_island['pos_y'] - current_island['pos_y']), 2))

    return distance

def _get_island_from_list(map_id, islands):
    for island in islands:
        if island['map_id'] == map_id:
            return island
    # If no island is found, return None
    return None

def _get_island_name_by_id(map_id):
    s = select([map_table]).where(map_table.c.map_id == map_id)
    conn = engine.connect()
    island = conn.execute(s).fetchone()
    if island is None:
        return ''
    return island['island_name']
