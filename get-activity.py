# Get activities from my Strava account
import requests
import pandas as pd
from pandas import json_normalize
import json
import csv
import numpy as np


# Make Strava auth API call with your 
# client_code, client_secret and code
response = requests.post(
                    url = 'https://www.strava.com/oauth/token',
                    data = {
                            'client_id': 54544,
                            'client_secret': '3f5e522edca619c8b4432d59805d28d82839ed07',
                            'code': '8ca0c4766ddad1af1de6dec03ef60ca74622d62f',
                            'grant_type': 'authorization_code'
                            }
                )

### Different approach to be evaluated:
### https://github.com/mandieq/strava_related/blob/master/stravalib_sample.ipynb 


#Save json response as a variable
strava_tokens = response.json()
# Save tokens to file

with open('strava_tokens.json', 'w') as outfile:
    json.dump(strava_tokens, outfile)

# Open JSON file and print the file contents 
# to check it's worked properly
with open('strava_tokens.json') as check:
    data = json.load(check)
print(data)

# Now get activities
# Get the tokens from file to connect to Strava
with open('strava_tokens.json') as json_file:
    strava_tokens = json.load(json_file)

# Loop through all activities
url = "https://www.strava.com/api/v3/activities"
access_token = api_credentials['access_token']

# Get first page of activities from Strava with all fields
nacts = 1 # number of activities to fetch
r = requests.get(url + '?access_token=' + access_token + '&per_page=' + str(nacts))
r = r.json()
    
df = json_normalize(r)
df.to_csv('strava_activities_all_fields.csv')

# Get kudoers per activity
act_ids = df['id']

# Initial empty DF
kudoers_current = pd.DataFrame()
for thisid in act_ids:
    r = requests.get(url + '/' + str(thisid) + '/kudos' + '?access_token=' + access_token)
    r = r.json()
    kudoers = json_normalize(r)
    kudoers['id'] = pd.DataFrame(np.repeat(thisid, kudoers.shape[0]))
    kudoers = kudoers.reset_index(drop=True)
    kudoers_current = pd.concat([kudoers_current, kudoers], axis=0)

kudoers_current.to_csv('kudoers_with_activity_id.csv')


with open('.secret/api_credentials.json', 'r') as f:
    api_credentials = json.load(f)
    client_id = api_credentials['client_id']
    client_secret = api_credentials['client_secret']
    refresh_token = api_credentials['refresh_token']
