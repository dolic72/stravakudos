import json
import csv
import requests
import numpy as np
import time
import pickle
import pandas as pd
from stravalib.client import Client
import urllib.parse
client = Client()

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

# One time process to generate initial access token.
# Follows procedure described here: 
# https://github.com/mandieq/strava_related/blob/master/stravalib_sample.ipynb 

url = client.authorization_url(client_id=client_id, redirect_uri='http://127.0.0.1:5000/authorization', scope=['read_all','profile:read_all','activity:read_all'] )
urllib.parse.unquote(url)
# Code copied from url result:
code = "0644dca0cd13028a48ce5df1d8f1aac0870fc680"
access_token = client.exchange_code_for_token(
    client_id = client_id, 
    client_secret = client_secret, 
    code = code
    )

api_credentials['access_token'] = access_token['access_token']
api_credentials['refresh_token'] = access_token['refresh_token']
with open('.secret/api_credentials.json', 'w') as f:
    json.dump(api_credentials, f)
