from sqlalchemy import create_engine, MetaData
from sqlalchemy import Table, Column, Integer, String, DateTime, Enum, ForeignKey, Sequence, select
import enum
from datetime import datetime
import os

if 'PR_DB_CONNECTOR' in os.environ:
    engine = create_engine(os.environ['DEMOAPP_DB_CONNECTOR'], convert_unicode=True)
else:
    engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True, echo=True)

metadata = MetaData()

# Users Table
users = Table('users', metadata,
   Column('id', Integer, Sequence('user_id_seq'), primary_key=True),
   Column('username', String(50)),
   Column('fullname', String(50)),
   Column('password', String(64)),
   Column('salt', String(12)),
   Column('lvl', Integer),
   Column('balance', Integer),
   Column('last_calculated', DateTime)
)

# Fleets Table
class FleetStatus(enum.Enum): # Need to wait until sqlalchemy 1.1 until we can just use the Enum :(
    active = 'ACTIVE'
    in_transit = 'IN_TRANSIT'
    destroyed = 'DESTROYED'

fleets = Table('fleets', metadata,
    Column('fleet_id', Integer, Sequence('fleet_id_seq'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('status', Enum('ACTIVE', 'IN_TRANSIT', 'DESTROYED')),
    Column('fleet_num', Integer),
    Column('island_id', Integer),
    Column('island_not_before', DateTime)
)

ships = Table('ships', metadata,
    Column('ship_id', Integer, Sequence('ship_id_seq'), primary_key=True),
    Column('class', String(40)),
    Column('power', Integer),
    Column('min_lvl', Integer),
    Column('cost', Integer)
)

fleet_ships = Table('fleet_ships', metadata,
    Column('fs_id', Integer, Sequence('fs_id_seq'), primary_key=True),
    Column('ship_class', String(40), ForeignKey('ships.class'), nullable=False),
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
        ins = users.insert()
        conn.execute(ins, username='jakel', fullname='Dan Jakel', salt='IQPKS7OWVHZH',
            password='26e8da140fd1adbcf52eb8a46a602e6be889d9cfc3dd21cb791c660039eff84f',
            lvl=1, balance=5000, last_calculated=datetime.now())

        ships_ins = ships.insert()
        conn.execute(ships_ins, [
            {'class': 'Gunboat', 'power': 2, 'min_lvl': 1, 'cost': 100},
            {'class': 'Schooner', 'power': 6, 'min_lvl': 2, 'cost': 500},
            {'class': 'Brig', 'power': 12, 'min_lvl': 5, 'cost': 1000},
            {'class': 'Frigate', 'power': 24, 'min_lvl': 10, 'cost': 10000},
            {'class': 'Man of War', 'power': 48, 'min_lvl': 20, 'cost': 50000},
            {'class': 'Jackdor', 'power': 58, 'min_lvl': 25, 'cost': 75000}
        ])
        print("finished inserts")
