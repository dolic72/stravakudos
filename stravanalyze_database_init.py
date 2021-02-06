import psycopg2
import psycopg2.extras as extras
import json

# database credentials
with open('.secret/postgres_credentials.json', 'r') as f:
    postgres_credentials = json.load(f)
    host = postgres_credentials['host']
    database = postgres_credentials['database']
    user = postgres_credentials['user']
    password = postgres_credentials['password']


# open connection to database
conn = psycopg2.connect(host=host, database=database, user=user, password=password)
# create cursor object
cur = conn.cursor()

# write SQL query
create_table_activities_query = """
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
    start_latlng CHARACTER VARYING(125),
    end_latlng CHARACTER VARYING(125),
    kudos_count SMALLINT,
    average_temp CHARACTER VARYING(10),
    has_heartrate BOOLEAN,
    gear_id CHARACTER VARYING(10),
    timezone CHARACTER VARYING(125),
    utc_offset INT,
    suffer_score NUMERIC,
    photos CHARACTER VARYING(255),
    workout_type INT
);
"""

create_table_gear_query = """
CREATE TABLE gear (
    id CHARACTER VARYING(64) PRIMARY KEY,
    name CHARACTER VARYING(255) NOT NULL,
    brand_name CHARACTER VARYING(125),
    distance NUMERIC
);
"""

create_table_kudoers_query = """
CREATE TABLE kudoers (
    firstname CHARACTER VARYING(255) NOT NULL,
    lastname CHARACTER VARYING(12),
    id BIGINT
);
"""

create_table_photos_query = """
CREATE TABLE photos (
    activity_id BIGINT,
    unique_id CHARACTER VARYING(255),
    url CHARACTER VARYING(2048)
);
"""


# commit tables to database
cur.execute("DROP TABLE IF EXISTS activities;")
cur.execute("DROP TABLE IF EXISTS gear;")
cur.execute("DROP TABLE IF EXISTS kudoers;")
cur.execute("DROP TABLE IF EXISTS photos;")

conn.commit()

cur.execute(create_table_activities_query)
conn.commit()

cur.execute(create_table_gear_query)
conn.commit()

cur.execute(create_table_kudoers_query)
conn.commit()

cur.execute(create_table_photos_query)
conn.commit()
