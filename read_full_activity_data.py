import time
import datetime
import pickle
import pandas as pd
import numpy as np
import json
import csv
import requests
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



my_activities = get_activities("2020-12-01 00:00:00")
