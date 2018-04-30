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

    return con, meta #returning con keeps you connected to the database, using con.execute('sql_syntax_here') excecutes and sql command.


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

    string = r'java -jar osm2po-core-5.2.43-signed.jar prefix={} {} '.format(prefix_name, geofabriklink)
    print(string)

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

def create_spatial_index(tablename = 'osm_nl_2po_4pgr', geometry = '(geom_way)'):

	# Normal index
	con.execute('CREATE INDEX idx_osm_nl_2po_4pgr_id ON public.{}(id)'.format(tablename))

	# Spatial index
	con.execute('CREATE INDEX osm2po_gindx ON {} USING GIST {}'.format(tablename, geometry))


def test_a_star(tablename = 'osm_nl_2po_4pgr'):
	''' 
	http://pgrouting.org/docs/foss4g2008/ch08.html
	osm2po already created x1 y1 etc.
	'''

	string = r"SELECT seq, node, edge, b.geom_way, b.osm_name FROM pgr_astar('SELECT id, source, target, cost ,reverse_cost, x1, y1, x2, y2 FROM osm_nl_2po_4pgr', 2, 12, heuristic:= 5) a LEFT join osm_nl_2po_4pgr b ON (a.edge = b.id);"
	a_star = con.execute(string)#.fetchall
	for x in a_star:
		print x


def create_a_star_route():
	string = r"CREATE TABLE route AS SELECT seq, node, edge, b.geom_way, b.osm_name FROM pgr_astar('SELECT id, source, target, cost ,reverse_cost, x1, y1, x2, y2 FROM osm_nl_2po_4pgr', 2, 12, heuristic:= 5) a LEFT join osm_nl_2po_4pgr b ON (a.edge = b.id);"
	a_star = con.execute(string)#.fetchall
	for x in a_star:
		print x


def create_ped_car_cycle_view():
	''' This function creates three seperate views for cars, cyclist and pedestrians respectively. More information on the values can be found  at :
		http://vesaliusdesign.com/2016/03/osm2pos-flag-field-explained/
		https://gis.stackexchange.com/questions/116701/what-does-the-values-in-column-clazz-osm2po-mean
		The use of views enables us to enable routing with different travel modes.

		Voor oscar: Een view is een soort selectie, maar dan zonder dingen dubbel op te slaan. Je voorkomt dus redundancy.
		'''



	#View of roads for cars
	con.execute('CREATE VIEW vehicle_net AS SELECT id as id, source::integer, target::integer, cost * 3600 as cost, reverse_cost * 3600 as reverse_cost FROM osm_nl_2po_4pgr WHERE clazz in (11,12,13,14,15,16,21,22,31,32,41,42,43,51,63)')

	#View of roads for cyclist
	con.execute('CREATE VIEW cycle_net AS SELECT id as id, source::integer, target::integer, cost * 3600 as cost, reverse_cost * 3600 as reverse_cost FROM osm_nl_2po_4pgr WHERE clazz in (31,32,41,42,43,51,63,62,71,72,81)')

	#View of roads for pedestrians
	con.execute('CREATE VIEW pedestrian_net AS SELECT id as id, source::integer, target::integer, cost * 3600 as cost, reverse_cost * 3600 as reverse_cost FROM osm_nl_2po_4pgr WHERE clazz in (63,62,71,72,91,92)')

	#check amount of nodes per view
	vehicle_count = con.execute('SELECT count(*) FROM vehicle_net').fetchall()
	print vehicle_count

	cycle_count = con.execute('SELECT count(*) FROM cycle_net').fetchall()
	print cycle_count

	pedestrian_count = con.execute('SELECT count(*) FROM pedestrian_net').fetchall()
	print pedestrian_count



'''
Probaly not using this


def pbf_to_osm(osmconvert_folder = r'C:\Program Files\PostgreSQL\10\bin>', file_folder = r'D:\Downloads\\', file_name = r'netherlands-latest.osm.pbf', out_name = r'osm_nl'):
	#trying to get a better organised road network in there
	string = r'{}'.format(osmconvert_folder)
	os.chdir(string)

	string1 = r'osmconvert64-0.8.8p --drop-author --drop-version --out-osm {}{} > {}.osm'.format(file_folder, file_name, out_name)
	os.system(string1)

def osm2pgrouting(osm2pgrouting_folder = r'C:\\Program Files\PostgreSQL\10\bin', file_folder = r'D:\TEMP', input_file = r'roads_nl.osm', dbname = r'osm_nl_new', username = r'postgres', password=r'):
	#trying to get a better organised road network in there
	string = r'{}'.format(osm2pgrouting_folder)
	os.chdir(string)

	string1 = r'osm2pgrouting --f {}\\{} --conf mapconfig.xml --dbname {} --username {} --password {} --clean --addnodes --tags --attributes'.format(file_folder, input_file, dbname, username, password)
	os.system(string1)
'''

	
####osmfilter D:\Temp\nl.osm --keep="highway=" -o=D:\Temp\roads_nl.osm <---- read this

#def main():
	#MAIN EXECUTION
# create_postgres_db('osm')
con, meta = connect_postgres_db('osm')
# create_postgis_pgrouting()
	# add_shapefile_to_postgress()
# query_100_result_of_table('roads')
	#create_and_check_topology('roads')
	#print_table_columns('osm_nl_2po_4pgr')
# osm2po_roads()
# import_osm2po()
	# import_osm2po()
# create_spatial_index()
#create_ped_car_cycle_view()
# test_a_star()
create_a_star_route()
	#
#if __name__ == "__main__":
#    main()
