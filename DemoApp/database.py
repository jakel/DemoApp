from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, Integer, Float, String, DateTime, Enum, ForeignKey, Sequence, select
import enum
from datetime import datetime
import os

if 'PR_DB_CONNECTOR' in os.environ:
    # eg. mysql://scott:tiger@localhost/foo
    engine = create_engine(os.environ['PR_DB_CONNECTOR'], convert_unicode=True)
else:
    engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True, echo=True)

metadata = MetaData()

# Users Table
users = Table('users', metadata,
   Column('user_id', Integer, Sequence('user_id_seq'), primary_key=True),
   Column('username', String(50)),
   Column('fullname', String(50)),
   Column('password', String(64)),
   Column('salt', String(12)),
   Column('lvl', Float),
   Column('balance', Integer),
   Column('last_calculated', DateTime)
)

# Map Tables
map_table = Table('map', metadata,
    Column('map_id', Integer, Sequence('map_id_seq'), primary_key=True),
    Column('island_name', String(40)),
    Column('pos_x', Integer),
    Column('pos_y', Integer)
)

# Ships Table
ships = Table('ships', metadata,
    Column('ship_id', Integer, Sequence('ship_id_seq'), primary_key=True),
    Column('type', String(40)),
    Column('power', Integer),
    Column('min_lvl', Integer),
    Column('cost', Integer),
    Column('build_speed', Integer)
)

# Fleets Table
class FleetStatus(enum.Enum): # Need to wait until sqlalchemy 1.1 until we can just use the Enum :(
    active = 'ACTIVE'
    in_transit = 'IN_TRANSIT'
    destroyed = 'DESTROYED'

fleets = Table('fleets', metadata,
    Column('fleet_id', Integer, Sequence('fleet_id_seq'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.user_id'), nullable=False),
    Column('status', Enum('ACTIVE', 'IN_TRANSIT', 'DESTROYED')),
    Column('fleet_num', Integer),
    Column('island_id', Integer, ForeignKey('map.map_id')),
    Column('island_not_before', DateTime)
)

fleet_ships = Table('fleet_ships', metadata,
    Column('fs_id', Integer, Sequence('fs_id_seq'), primary_key=True),
    Column('ship_type', String(40), ForeignKey('ships.type'), nullable=False),
    Column('fleet_id', Integer, ForeignKey('fleets.fleet_id'), nullable=False),
    Column('number', Integer),
    Column('status', Enum('ACTIVE', 'BUILDING', 'DESTROYED')),
    Column('not_before', DateTime)
)



def init_db(debug=True):
    #import tables from various files
    #from DemoApp import users

    # if in debug mode, add some basic data to sqlite
    if debug:
        metadata.create_all(bind=engine)
        print("running inserts")
        conn = engine.connect()
        user_count = conn.execute(select([users]).where(users.c.username == 'jakel').count()).scalar()
        if user_count == 0:
            ins = users.insert()
            conn.execute(ins, username='jakel', fullname='Dan Jakel', salt='IQPKS7OWVHZH',
                password='26e8da140fd1adbcf52eb8a46a602e6be889d9cfc3dd21cb791c660039eff84f',
                lvl=0, balance=5500, last_calculated=datetime.now())

        ship_count = conn.execute(select([ships]).count()).scalar()

        if ship_count == 0:
            ships_ins = ships.insert()
            conn.execute(ships_ins, [
                {'type': 'Gunboat', 'power': 2, 'min_lvl': 0, 'cost': 100, 'build_speed': 60},
                {'type': 'Schooner', 'power': 6, 'min_lvl': 2, 'cost': 500, 'build_speed': 300},
                {'type': 'Brig', 'power': 12, 'min_lvl': 5, 'cost': 1000, 'build_speed': 600},
                {'type': 'Frigate', 'power': 24, 'min_lvl': 10, 'cost': 10000, 'build_speed': 6000},
                {'type': 'Man of War', 'power': 48, 'min_lvl': 20, 'cost': 50000, 'build_speed': 30000},
                {'type': 'Jackdaw', 'power': 58, 'min_lvl': 25, 'cost': 75000, 'build_speed': 45000}
            ])

        map_count = conn.execute(select([map_table]).count()).scalar()

        if map_count == 0:
            map_ins = map_table.insert()
            conn.execute(map_ins, [
                {'island_name': 'Havana', 'pos_x': 228 , 'pos_y': 378},
                {'island_name': 'Miami', 'pos_x': 452 , 'pos_y': 128},
                {'island_name': 'Nassau', 'pos_x': 600 , 'pos_y': 200},
                {'island_name': 'Cozumel', 'pos_x': 118 , 'pos_y': 556},
                {'island_name': 'Santiago', 'pos_x': 645 , 'pos_y': 617},
                {'island_name': 'Pole', 'pos_x': 81 , 'pos_y': 517},
                {'island_name': 'Kingston', 'pos_x': 615 , 'pos_y': 831},
                {'island_name': 'Jeremie', 'pos_x': 816 , 'pos_y': 765},
            ])
        print("finished inserts")
