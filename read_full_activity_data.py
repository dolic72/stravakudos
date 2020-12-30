import time
import datetime
import pickle
import pandas as pd
import numpy as np
import json
import csv
import sys
import requests
import psycopg2
import psycopg2.extras as extras
from stravalib.client import Client
from stravalib.exc import RateLimitExceeded

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


def get_activity_summaries(date_since=""):
    if date_since == "":
        date_since = str(datetime.datetime.now() - datetime.timedelta(1))
    df_perm = pd.DataFrame() # initialize empty dataframe

    activities = client.get_activities(after=date_since)
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
            'start_latlng',
            'end_latlng',
            'kudos_count',
            'average_temp',
            'has_heartrate',
            'gear_id',
            'timezone',
            'utc_offset',
            'suffer_score',
            'workout_type'
            ]

    data = []
    for activity in activities:
        my_dict = activity.to_dict()
        data.append([activity.id]+[my_dict.get(x) for x in my_cols])

    my_cols.insert(0, 'id')
    df = pd.DataFrame(data, columns=my_cols) # data from this iteration
    df = df[df['type'] == "Run"]
    df = df.reset_index(drop=True)
    df_perm = pd.concat([df_perm, df], axis=0)
    # Some "repair" stuff:
    df_perm = df_perm[df_perm["moving_time"].notnull()]
    df["suffer_score"] = df["suffer_score"].fillna(0)
    df["workout_type"] = df["workout_type"].fillna(0)
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

def get_kudoers(activity_meta, rate_limit = 90):
    act_ids = activity_meta.id
    df_ret = pd.DataFrame()
    fields = ['firstname', 'lastname']
    cnt = 0
    for thisid in act_ids:
        try:
            if cnt >= rate_limit:
                time.sleep(1000)
                cnt = 0
            kudoers = client.get_activity_kudos(thisid)
            cnt += 1
            for k in kudoers:
                df = pd.DataFrame([{fn: getattr(k, fn) for fn in fields}])
                df['id'] = thisid 
                df = df.reset_index(drop = True)
                df_ret = pd.concat([df_ret, df], axis=0)
        except (Exception, RateLimitExceeded) as x:
            print("Error: {}".format(x))
            print("Result might be incomplete")
            return df_ret
    return df_ret

def get_photos(activity_meta, rate_limit = 90):
    act_ids = activity_meta.id
    df_ret = pd.DataFrame()
    cnt = 0
    for thisid in act_ids:
        try:
            if cnt >= rate_limit:
                time.sleep(1000)
                cnt = 0
            photos = client.get_activity_photos(thisid, size = 2048)
            cnt += 1
            if photos:
                my_cols = ['activity_id', 'unique_id']
                data = []
                for p in photos:
                    d = p.to_dict()
                    data.append([d.get(c) for c in my_cols])
                    df = pd.DataFrame(data, columns = my_cols)
                    df['url'] = d["urls"][list(d["sizes"].keys())[0]]
                    df = df.reset_index(drop = True)
                    df_ret = pd.concat([df_ret, df], axis=0)
        except (Exception, RateLimitExceeded) as x:
            print("Error: {}".format(x))
            print("Result might be incomplete")
            return df_ret
    df_ret.drop_duplicates()
    return df_ret

def write_db(con, df, table, pk = 'id', page_size=100):
    if not(df.empty):
        # Get all reserved IDs:
        ids = []
        with con:
            with con.cursor() as sc:
                try:
                    qry = "SELECT distinct {} FROM {} ;".format(pk, table)
                    sc.execute(qry)
                    ids = sc.fetchall()
                except (Exception, psycopg2.DatabaseError) as error:
                    print("Error: {}".format( error ))
        # Filter dataframe from reserved IDs:
        if ids:
            before = len(df)
            filter_ids = [item for t in ids for item in t] # convert tupled list
            df = df[~df[pk].isin(filter_ids)]
            print("Excluded {} id-values from insert.".format(before - len(df)))
        # Write part
        # Comma-separated dataframe columns
        cols = ','.join(list(df.columns))
        # SQL query to execute
        placeholder = "VALUES({})".format(','.join(['%s']*len(df.columns)))
        qry = "INSERT INTO {} ({}) {}".format(table, cols, placeholder)
        print("Start to insert {} new values:".format(len(df)))
        with con:
            with con.cursor() as c:
                try:
                    extras.execute_batch(c, qry, df.values, page_size)
                    con.commit()
                    print("Success!")
                except (Exception, psycopg2.DatabaseError) as e:
                    print("Error: {}".format(e))
                    con.rollback()
    else:
        print("{} dataframe has no data.".format(df))

### Execution part ###
# database credentials
with open('.secret/postgres_credentials.json', 'r') as f:
    postgres_credentials = json.load(f)
    host = postgres_credentials['host']
    database = postgres_credentials['database']
    user = postgres_credentials['user']
    password = postgres_credentials['password']

try:
    con = psycopg2.connect(host=host, database=database, user=user, password=password)
except psycopg2.DatabaseError as e:
    print("Error {}".format(e))
    sys.exit(1)

my_activities = get_activity_summaries("2020-01-01 00:00:00")
write_db(con, my_activities, "activities")
my_gear = get_gear_names(my_activities)
write_db(con, my_gear, "gear")
my_kudoes = get_kudoers(my_activities)
write_db(con, my_kudoes, "kudoers")
my_imgs = get_photos(my_activities)
write_db(con, my_imgs, "photos", pk = 'activity_id')

# close connection to database
con.close()

