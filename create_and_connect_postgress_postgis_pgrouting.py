


#Laurens, Oscar these are the necesarry modules you can install using pipinstal e.g, type in your commandline: 'python -m pip install geoalchemy2'.
from sqlalchemy import create_engine
from sqlalchemy import MetaData
import geoalchemy2 #Otherwise geom column is loaded wrong
import getpass
import os
import webbrowser

# some interesting slides: http://www.postgis.us/presentations/postgis_install_guide_22.html#/11

def create_postgres_db(databasename = 'Betty'):
    ''' creates a database at a localhost'''
    db_name = databasename

    #ask the user for a password and stores it in 'password'
    password = getpass.getpass()
    
    #create starting point
    engine = create_engine('postgresql://postgres:'+str(password)+'@localhost:5432/')

    #connect to starting point
    con = engine.connect()

    #enable sql
    con.execute('commit')

    #create database
    con.execute("CREATE DATABASE " + db_name)


def connect_postgres_db(db, user = 'postrgres', host = 'localhost', port = '5432'):
    '''Returns a connection and a metadata object'''
    
    #ask the user for a password and stores it in 'password'
    password = getpass.getpass()

    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(user, password, host, port, db)

    # The return value of create_engine() is our connection object
    con = create_engine(url, client_encoding='utf8')

    # We then bind the connection to MetaData()
    meta = MetaData(bind=con, reflect=True)

    return con, meta #returning con keeps you connected to the database, using con.execute('sql_syntax_here') excecutes and sql command.


def create_postgis_pgrouting():
    ''' Creates the necessary spatial plugins such as postgis and pgrouting within a database. The 'con' object is the engine created using the 'connect_postgres_db()' function. the 'execute()' functions takes a SQL statement which is send to the postgres DB. The '.fetchall()' retrieves all the information and stores in in a python readable object.
    
    The last part of the function checks the version of the installed extensions.
    '''
    
    con.execute('CREATE EXTENSION postgis')
    con.execute('CREATE EXTENSION hstore')
    con.execute('CREATE EXTENSION fuzzystrmatch')
    con.execute('CREATE EXTENSION postgis_tiger_geocoder')
    con.execute('CREATE EXTENSION postgis_topology')
    con.execute('CREATE EXTENSION pgrouting')

    # Check if working
    result1 = con.execute('SELECT postgis_full_version()').fetchall()
    print(result1)

    result2 = con.execute('SELECT * FROM pgr_version()').fetchall()
    print(result2)


def osm2po_roads(geofabriklink = 'http://download.geofabrik.de/europe/netherlands-latest.osm.pbf', prefix_name= 'osm_nl', osm2po_folder = r'D:\Documenten\GIMA\Module 6\Datas'):

    # Sets the working directory to osm2po folder
    os.chdir(osm2po_folder)

    # The version of osm2po version used can be found at: http://osm2po.de/releases/osm2po-5.2.43.zip . Extract this to your computer, make sure JAVA is installed and is set within your PATH environment. More info can be found at http://osm2po.de/ .

    # The configuration file used in osm2po is uploaded on github with the name osm2po.config. Use this one to extract car, cycling and pedestrian roads and exclude trains boat and tram roads.

    # Executes a string in the commandline of your pc. In this case, a program called osm2po extracts the latest Dutch osm files, containing all object types e.g., houses, parks, roads, shops. The program selects only the roads, and converts it to a file that can be imported by a Database Management System (DBBMS).

    string = r'java -jar osm2po-core-5.2.43-signed.jar prefix={} {} '.format(prefix_name, geofabriklink)
    os.system(string)


def import_osm2po(prefix_name= 'osm_nl', osm2po_folder = r'D:\Documenten\GIMA\Module 6\Datas', dbname= 'osm', dbuser= 'postgres'):

    # Sets the working directory to the place where osm2po created a SQL file.
    string = r'{}\\{}'.format(osm2po_folder, prefix_name)
    os.chdir(string)

    # Imports the osm2po sql file into your database using your commandline.
    string1 = r'psql -d {} -U {} -f {}_2po_4pgr.sql'.format(dbname, dbuser, prefix_name)
    os.system(string1)


def create_spatial_index(tablename = 'osm_nl_2po_4pgr', geometry = '(geom_way)'):
    '''This function creates a normal and spatial index on the road network to speed up queries'''

    # Normal index
    con.execute('CREATE INDEX idx_osm_nl_2po_4pgr_id ON public.{}(id)'.format(tablename))

    # Spatial index
    con.execute('CREATE INDEX osm2po_gindx ON {} USING GIST {}'.format(tablename, geometry))


def test_a_star(tablename = 'osm_nl_2po_4pgr'):
    ''' 
    This functions tests your road network using the a* shortest path alghorithm and delivers print the output based on the standard osm2po column names.
    http://pgrouting.org/docs/foss4g2008/ch08.html
    osm2po already created x1 y1 etc.
    '''

    string = r"SELECT seq, node, edge, b.geom_way, b.osm_name FROM pgr_astar('SELECT id, source, target, cost ,reverse_cost, x1, y1, x2, y2 FROM {}', 2, 12, heuristic:= 5) a LEFT join {} b ON (a.edge = b.id);"
    a_star = con.execute(string)#.fetchall
    for x in a_star:
        print(x)


def create_a_star_route(new_tablename = 'route', road_network_table = 'osm_nl_2po_4pgr'):
    '''
    This functions creates a new database based on the standard osm2po column names.
    '''

    string = r"CREATE TABLE {} AS SELECT seq, node, edge, b.geom_way, b.osm_name FROM pgr_astar('SELECT id, source, target, cost ,reverse_cost, x1, y1, x2, y2 FROM {}', 2, 12, heuristic:= 5) a LEFT join {} b ON (a.edge = b.id);".format(new_tablename, road_network_table, road_network_table)
    a_star = con.execute(string)#.fetchall
    for x in a_star:
        print(x)


def create_ped_car_cycle_view():
    ''' This function creates three seperate views for cars, cyclist and pedestrians respectively. More information on the values can be found  at :
        http://vesaliusdesign.com/2016/03/osm2pos-flag-field-explained/
        https://gis.stackexchange.com/questions/116701/what-does-the-values-in-column-clazz-osm2po-mean
        The use of views enables us to enable routing with different travel modes.

        Voor Laurens en Oscar: Een view is een soort selectie, maar dan zonder dingen dubbel op te slaan. Je voorkomt dus redundancy.
        '''

    #View of roads for cars
    con.execute('CREATE VIEW vehicle_net AS SELECT id as id, source::integer, target::integer, cost * 3600 as cost, reverse_cost * 3600 as reverse_cost FROM osm_nl_2po_4pgr WHERE clazz in (11,12,13,14,15,16,21,22,31,32,41,42,43,51,63)')

    #View of roads for cyclist
    con.execute('CREATE VIEW cycle_net AS SELECT id as id, source::integer, target::integer, cost * 3600 as cost, reverse_cost * 3600 as reverse_cost FROM osm_nl_2po_4pgr WHERE clazz in (31,32,41,42,43,51,63,62,71,72,81)')

    #View of roads for pedestrians
    con.execute('CREATE VIEW pedestrian_net AS SELECT id as id, source::integer, target::integer, cost * 3600 as cost, reverse_cost * 3600 as reverse_cost FROM osm_nl_2po_4pgr WHERE clazz in (63,62,71,72,91,92)')



    #The following lines select the total amount of nodes/egdes within the created views and the original road network. These outputs should obviously differ.
    osm_count = con.execute('SELECT count(*) FROM osm_nl_2po_4pgr').fetchall()
    print(osm_count)

    vehicle_count = con.execute('SELECT count(*) FROM vehicle_net').fetchall()
    print(vehicle_count)

    cycle_count = con.execute('SELECT count(*) FROM cycle_net').fetchall()
    print(cycle_count)

    pedestrian_count = con.execute('SELECT count(*) FROM pedestrian_net').fetchall()
    print(pedestrian_count)


def add_sql_function(sql_location_file = r'D:\Documenten\GIMA\Module 6\Datas\create_function_astar.sql', dbname = 'osm'):

    # Add a sql function to your database, e.g, the coordinates to dijkstra output
    string1 = r'psql -U postgres -d {} -a -f {}'.format(dbname, sql_location_file)
    os.system(string1)



# First create a database, connect to it, and add spatial extensions.
create_postgres_db('osm')
con, meta = connect_postgres_db('osm')
create_postgis_pgrouting()

# Create a SQL dump containing topology of and osm.pbf file.
osm2po_roads()

# Quit the commandline and restart from this function onwards. This will import the sql dump create a spatial index, create separate views for several travel modes.
# import_osm2po()
# create_spatial_index()
# create_ped_car_cycle_view()

# When de database is fully functioning it will test the low-level a star function.
    # test_a_star()
    # create_a_star_route()

# Implement a self made sql function for geoserver, e.g, dijkstra from coordinates. Currently working on a-star.
    # add_sql_function()


if __name__ == "__main__":
   main()







###BELOW DEPRECATED FUNCTIONS ARE SHOWN, NOT IMPORTANT @LAURENS, OSCAR
"""
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
    os.system(string1) """