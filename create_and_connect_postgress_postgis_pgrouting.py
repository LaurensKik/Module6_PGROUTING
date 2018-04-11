from sqlalchemy import create_engine
from sqlalchemy import MetaData
import getpass

# some interesting slides: http://www.postgis.us/presentations/postgis_install_guide_22.html#/11

def create_postgres_db(databasename):
	db_name = databasename

	#ask password
	password = getpass.getpass()
	
	#create starting point
	engine = create_engine('postgresql://postgres:'+str(password)+'@localhost:5432/')

	#connect to starting point
	con = engine.connect()

	#enable sql
	con.execute('commit')

	#create database
	con.execute("CREATE DATABASE " +db_name)

def connect_postgres_db(db):
    '''Returns a connection and a metadata object'''
    # We connect with the help of the PostgreSQL URL
    # postgresql://federer:grandestslam@localhost:5432/tennis
    user = 'postgres'
    password = getpass.getpass()
    host='localhost'
    port=5432

    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(user, password, host, port, db)

    # The return value of create_engine() is our connection object
    con = create_engine(url, client_encoding='utf8')

    # We then bind the connection to MetaData()
    meta = MetaData(bind=con, reflect=True)

    return con, meta


def create_postgis_pgrouting():
	con.execute('CREATE EXTENSION postgis')
	con.execute('CREATE EXTENSION hstore')
	con.execute('CREATE EXTENSION fuzzystrmatch')
	con.execute('CREATE EXTENSION postgis_tiger_geocoder')
	con.execute('CREATE EXTENSION postgis_topology')
	con.execute('CREATE EXTENSION pgrouting')

	#check if working
	result1 = con.execute('SELECT postgis_full_version()')
	for r in result1:
		print(r)

	result2 = con.execute('SELECT * FROM pgr_version()')
	for r in result2:
		print(r)





create_postgres_db('osm')
con, meta = connect_postgres_db('osm')
create_postgis_pgrouting()