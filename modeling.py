import tensorflow as tf
from tensorflow import keras
import psycopg2
import json
import datetime

# database credentials
with open('.secret/postgres_credentials.json', 'r') as f:
    postgres_credentials = json.load(f)
    host = postgres_credentials['host']
    database = postgres_credentials['database']
    user = postgres_credentials['user']
    password = postgres_credentials['password']


# open connection to database
con = psycopg2.connect(host=host, database=database, user=user, password=password)

qry_fields = "id, start_date, distance, moving_time, total_elevation_gain"

# Get data for modelling
with con:
    with con.cursor() as sc:
        try:
            qry = "SELECT {} FROM public.activities ;".format(qry_fields)
            sc.execute(qry)
            df = sc.fetchall()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: {}".format( error ))


# convert list to df