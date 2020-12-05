import json
import csv
import requests
import numpy as np

# https://medium.com/swlh/building-an-automated-data-pipeline-using-the-strava-api-30b0ef0fb42f

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
access_token = api_credentials['access_token']