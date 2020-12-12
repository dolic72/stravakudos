import time
import datetime
import pickle
import pandas as pd
import numpy as np
import json
import csv
import requests
import psycopg2
import psycopg2.extras as extras
from stravalib.client import Client

client = Client()

# MY_STRAVA_CLIENT_ID, MY_STRAVA_CLIENT_SECRET = open('client.secret').read().strip().split(',')
# print ('Client ID and secret read from file'.format(MY_STRAVA_CLIENT_ID) )

# url = client.authorization_url(client_id=MY_STRAVA_CLIENT_ID, redirect_uri='http://127.0.0.1:5000/authorization', scope=['read_all','profile:read_all','activity:read_all'])
# import urllib.parse
# urllib.parse.unquote(url)

# CODE = '8d46ff9a7def9d54a0eaf7c1dae1cb62cc7ac203'

# access_token = client.exchange_code_for_token(client_id=MY_STRAVA_CLIENT_ID, 
# client_secret=MY_STRAVA_CLIENT_SECRET, 
# code=CODE)

# store API credentials
with open('.secret/api_credentials.json', 'r') as f:
    api_credentials = json.load(f)
    client_id = api_credentials['client_id']
    client_secret = api_credentials['client_secret']
    refresh_token = api_credentials['refresh_token']

# make POST request to Strava API
req = requests.post("https://www.strava.com/oauth/token?client_id={}&client_secret={}&refresh_token={}&grant_type=refresh_token".format(client_id, client_secret, refresh_token)).json()

# update API credentials file
api_credentials['access_token'] = req['access_token']
api_credentials['refresh_token'] = req['refresh_token']

with open('.secret/api_credentials.json', 'w') as f:
    json.dump(api_credentials, f)

# store new access token
client.access_token = api_credentials['access_token']
client.refresh_token = api_credentials['refresh_token']
client.token_expires_at = api_credentials['expires_at']

athlete = client.get_athlete()
# All fields
# athlete.to_dict()


def get_activities(date_since):
    mindate = str(datetime.datetime.now())
    df_perm = pd.DataFrame() # initialize empty dataframe

    while date_since < mindate:
        activities = client.get_activities(limit=100)
        my_cols = ['name',
                'start_date_local',
                'start_date',
                'type',
                'distance',
                'moving_time',
                'elapsed_time',
                'total_elevation_gain',
                'elev_high',
                'elev_low',
                'average_speed',
                'max_speed',
                'average_heartrate',
                'max_heartrate',
                'start_latitude',
                'start_longitude',
                'kudos_count',
                'average_temp',
                'has_heartrate',
                'calories',
                'gear_id']

        data = []
        for activity in activities:
            my_dict = activity.to_dict()
            data.append([activity.id]+[my_dict.get(x) for x in my_cols])

        my_cols.insert(0, 'id')
        df = pd.DataFrame(data, columns=my_cols) # data from this iteration
        df = df[df['type'] == "Run"]
        df = df.reset_index(drop=True)
        df_perm = pd.concat([df_perm, df], axis=0)
        mindate = min(df_perm['start_date_local'])
        df_perm = df_perm[df_perm['start_date_local'] > date_since]
    return df_perm

def get_gear_names(activity_meta):
    gearid = activity_meta['gear_id']
    fields = ['id', 'name', 'brand_name']
    df_ret = pd.DataFrame()
    for thisid in gearid:
        gear_data = client.get_gear(thisid)
        df = pd.DataFrame([{fn: getattr(gear_data, fn) for fn in fields}])
        dst = getattr(gear_data, "distance")
        df['distance'] = [dst.num]
        df = df.reset_index(drop=True)
        df_ret = pd.concat([df_ret, df], axis=0)
    return df_ret

# store database credentials
with open('.secret/postgres_credentials.json', 'r') as f:
    postgres_credentials = json.load(f)
    host = postgres_credentials['host']
    database = postgres_credentials['database']
    user = postgres_credentials['user']
    password = postgres_credentials['password']

# open connection to database
conn = psycopg2.connect(host=host, database=database, user=user, password=password)# create cursor object
cur = conn.cursor()

# write SQL query
create_table_query = """
CREATE TABLE activities (
    id BIGINT PRIMARY KEY,
    name CHARACTER VARYING(255) NOT NULL,
    start_date_local CHARACTER(64) NOT NULL,
    start_date CHARACTER(64) NOT NULL,
    type CHARACTER VARYING(64) NOT NULL,
    distance NUMERIC NOT NULL,
    moving_time CHARACTER VARYING(10) NOT NULL,
    elapsed_time CHARACTER VARYING(10) NOT NULL,
    total_elevation_gain NUMERIC,
    elev_high NUMERIC,
    elev_low NUMERIC,
    average_speed NUMERIC,
    max_speed NUMERIC,
    average_heartrate NUMERIC,
    max_heartrate NUMERIC,
    start_latitude NUMERIC,
    start_longitude NUMERIC,
    kudos_count SMALLINT,
    average_temp CHARACTER VARYING(10),
    has_heartrate CHARACTER VARYING(10),
    calories CHARACTER VARYING(10),
    gear_id CHARACTER VARYING(10)
);
"""

# commit table to database
cur.execute(create_table_query)
conn.commit()

def execute_batch(conn, df, table, page_size=100):
    """
    Using psycopg2.extras.execute_batch() to insert the dataframe
    """
    # Create a list of tupples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    # Comma-separated dataframe columns
    cols = ','.join(list(df.columns))
    # SQL query to execute
    query  = "INSERT INTO %s(%s) VALUES(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s)" % (table, cols)
    cursor = conn.cursor()
    try:
        extras.execute_batch(cursor, query, tuples, page_size)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("execute_batch() done")
    cursor.close()    



my_activities = get_activities("2020-10-01 00:00:00")
execute_batch(conn, my_activities, "activities")

# close connection to database
conn.close()
