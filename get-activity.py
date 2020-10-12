# Get activities from my Strava account
import requests
import pandas as pd
from pandas import json_normalize
import json
import csv
import numpy


# Make Strava auth API call with your 
# client_code, client_secret and code
response = requests.post(
                    url = 'https://www.strava.com/oauth/token',
                    data = {
                            'client_id': 54544,
                            'client_secret': '3f5e522edca619c8b4432d59805d28d82839ed07',
                            'code': '8e17d122de30160ff05c7fca28c6efcf885af3e5',
                            'grant_type': 'authorization_code'
                            }
                )

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
access_token = strava_tokens['access_token']

# Get first page of activities from Strava with all fields
r = requests.get(url + '?access_token=' + access_token + '&per_page=200')
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
