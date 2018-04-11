from sqlalchemy import create_engine
import getpass


def create_postgress_db(databasename):
	db_name = databasename

	#ask password
	password = getpass.getpass()
	
	#create starting point
	engine = create_engine('postgresql://postgres:'+str(password)+'@localhost:5432/')

	#connect to starting point
	conn = engine.connect()

	#enable sql
	conn.execute('commit')

	#create database
	conn.execute("CREATE DATABASE " +db_name)


create_postgress_db('osm3')
