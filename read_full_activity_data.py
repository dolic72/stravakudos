import time
import datetime
import pickle
import pandas as pd
import numpy as np
from stravalib.client import Client

import gpxpy
import gpxpy.gpx

client = Client()

MY_STRAVA_CLIENT_ID, MY_STRAVA_CLIENT_SECRET = open('client.secret').read().strip().split(',')
print ('Client ID and secret read from file'.format(MY_STRAVA_CLIENT_ID) )

url = client.authorization_url(client_id=MY_STRAVA_CLIENT_ID, redirect_uri='http://127.0.0.1:5000/authorization', scope=['read_all','profile:read_all','activity:read_all'])
import urllib.parse
urllib.parse.unquote(url)

CODE = '0f7c5fc7c0d7f715cbc13175e515a097eabf4b64'

access_token = client.exchange_code_for_token(client_id=MY_STRAVA_CLIENT_ID, 
client_secret=MY_STRAVA_CLIENT_SECRET, 
code=CODE)


## Read access token from file
with open('../access_token.pickle', 'wb') as f:
    pickle.dump(access_token, f)

# Refresh access token if necessary
if time.time() > access_token['expires_at']:
    print('Token has expired, will refresh')
    refresh_response = client.refresh_access_token(client_id=MY_STRAVA_CLIENT_ID, 
                                               client_secret=MY_STRAVA_CLIENT_SECRET, 
                                               refresh_token=access_token['refresh_token'])
    access_token = refresh_response
    with open('../access_token.pickle', 'wb') as f:
        pickle.dump(refresh_response, f)
    print('Refreshed token saved to file')

    client.access_token = refresh_response['access_token']
    client.refresh_token = refresh_response['refresh_token']
    client.token_expires_at = refresh_response['expires_at']
        
else:
    print('Token still valid, expires at {}'
          .format(time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(access_token['expires_at']))))

    client.access_token = access_token['access_token']
    client.refresh_token = access_token['refresh_token']
    client.token_expires_at = access_token['expires_at']

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
    for thisid in gearid:
        gear_data = client.get_gear(thisid)


def create_gpx(activity_meta):
    activity_ids = activity_meta['id']
    # types = ['time', 'distance', 'latlng', 'altitude', 'velocity_smooth', 'moving', 'grade_smooth', 'heartrate']
    types = ['time', 'latlng', 'altitude']
    for thisid in activity_ids:
        activity_data=client.get_activity_streams(thisid, types=types)
        # get start time for this activity
        starttime = activity_meta[activity_meta['id'] == thisid]['start_date'].values[0]

        ### Create gpx output
        gpx = gpxpy.gpx.GPX()

        # Create first track in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        for i in range(len(activity_data['time'].data)):
            lat = activity_data['latlng'].data[i][0]
            lon = activity_data['latlng'].data[i][1]
            ele = activity_data['altitude'].data[i]
            ts = pd.to_datetime(starttime) + datetime.timedelta(0, activity_data['time'].data[i])
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele, time=ts))

        filename = "strava_id_" + str(thisid) + ".gpx"
        with open(filename, "w") as f:
            f.write( gpx.to_xml())
        print("Generated file " + filename)

my_activities = get_activities("2020-09-12 00:00:00")
create_gpx(my_activities)