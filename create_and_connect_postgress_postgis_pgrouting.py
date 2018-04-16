from sqlalchemy import create_engine
from sqlalchemy import MetaData
import geoalchemy2 #Otherwise geom column is loaded wrong
import getpass
import os
import webbrowser

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
	#creates the necessary spatial plugins such as postgis and pgrouting within a database
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


def add_shapefile_to_postgress(shp_folder = r"C:\Users\Joris\Google Drive\Gima\Module_6\Module-6_groupwork\Data\OSM_SHAPES", shp_name = r"amsterdam_cyclepaths.shp", user = 'postgres', db = 'osm' ):
	
	#set working directory to shp folder
	os.chdir(shp_folder)
	
	# create string to execute in command line (outside of python)
	string = r'shp2pgsql -I "{}\\{}" public.roads | psql -U {} -d {}'.format(os.getcwd(), shp_name, user, db)
	print(string)

	#execute the formatted command in CMD
	os.system(string)

def query_100_result_of_table(tablename):
	''' Requires a current connection'''
	string = 'SELECT * FROM {} LIMIT 100'.format(tablename)
	result = con.execute(string)
	for r in result:
		print(r)

def print_table_columns(tablename):
	''' Requires a current connection'''
	result = con.execute('SELECT column_name FROM information_schema.columns WHERE table_name=\'{}\''.format(tablename))
	for r in result:
		print(r)

def create_and_check_topology(tablename):
	''' Requires a current connection, more info http://docs.pgrouting.org/2.3/en/doc/src/tutorial/tutorial.html'''
	#LOL DEZE DOET NIETS, niet gebruiken
	#create topology
	con.execute('ALTER TABLE {} ADD COLUMN "source" integer'.format(tablename))
	con.execute('ALTER TABLE {} ADD COLUMN "target" integer'.format(tablename))
	con.execute('select pgr_createTopology(\'{}\', 0.000001, \'geom\', \'gid\')'.format(tablename))
	#con.execute('select pgr_analyzegraph(\'{}\', 0.000001)'.format(tablename))
	#con.execute('select pgr_analyzeoneway(\'{}\',  s_in_rules, s_out_rules, t_in_rules, t_out_rules, direction)'.format(tablename))

def osm2po_roads(geofabriklink = 'http://download.geofabrik.de/europe/netherlands-latest.osm.pbf', prefix_name= 'osm_nl', osm2po_folder = r'D:\TEMP'):

	#set directory to osm2po folder
	os.chdir(osm2po_folder)

	string = r'java -jar osm2po-core-5.2.43-signed.jar prefix={} {}'.format(prefix_name, geofabriklink)
	print string

	os.system(string)

def import_osm2po(prefix_name= 'osm_nl', osm2po_folder = r'D:\TEMP'):

	string = r'{}\\{}'.format(osm2po_folder, prefix_name)
	os.chdir(string)

	string1 = r'psql -d osm -U postgres -f {}_2po_4pgr.sql'.format(prefix_name)
	os.system(string1)

	# string2 = r'psql -d osm -U postgres -f {}_2po_polyway.sql'.format(prefix_name)
	# os.system(string2)

	# string3 = r'psql -d osm -U postgres -f {}_2po_vertex.sql'.format(prefix_name)
	# os.system(string3)

#MAIN EXECUTION
#create_postgres_db('osm')
con, meta = connect_postgres_db('osm')
#create_postgis_pgrouting()
# add_shapefile_to_postgress()
# query_100_result_of_table('roads')
# create_and_check_topology('roads')
print_table_columns('osm_nl_2po_4pgr')
# osm2po_roads()
#import_osm2po()
