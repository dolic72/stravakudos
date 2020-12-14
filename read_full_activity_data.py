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

# athlete = client.get_athlete()
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
    gearid = activity_meta.gear_id.unique()
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

# database credentials
with open('.secret/postgres_credentials.json', 'r') as f:
    postgres_credentials = json.load(f)
    host = postgres_credentials['host']
    database = postgres_credentials['database']
    user = postgres_credentials['user']
    password = postgres_credentials['password']


def execute_batch(conn, df, table, pk = 'id', page_size=100):
    # Get all reserved IDs:
    select_cursor = conn.cursor()
    ids = []
    try:
        qry = "SELECT distinct id FROM " + table + ";"
        select_cursor.execute(qry)
        ids = select_cursor.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        select_cursor.close()
        return 1
    # Filter dataframe from reserved IDs:
    if ids:
        filter_ids = [item for t in ids for item in t] # convert tupled list
        df = df[~df[pk].isin(filter_ids)]
    select_cursor.close()
    """
    Using psycopg2.extras.execute_batch() to insert the dataframe
    """
    # Create a list of tuples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    # Comma-separated dataframe columns
    cols = ','.join(list(df.columns))
    # SQL query to execute
    query  = "INSERT INTO %s(%s) VALUES(" + ','.join(['%%s']*len(my_activities.columns)) + ")" % (table, cols)
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

### Execution part ###
conn = psycopg2.connect(host=host, database=database, user=user, password=password)# create cursor object
cur = conn.cursor()


my_activities = get_activities("2020-08-01 00:00:00")
execute_batch(conn, my_activities, "activities")
my_gear = get_gear_names(my_activities)

# close connection to database
conn.close()

