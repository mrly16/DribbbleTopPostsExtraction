from flask import Flask, render_template
import json
import requests_oauthlib
import webbrowser
import secret_data
from datetime import datetime
import psycopg2
import sys
import psycopg2.extras
from config import *


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
# user_list = ['WOLF_STEVE', 'outcrowd', 'studioMUTI', 'Tamarashvili', 'DmiT']
user_list = ['norde', 'Fireart-d', 'paperpillar', 'cuberto', 'netguru']


CLIENT_KEY = secret_data.client_key
CLIENT_SECRET = secret_data.client_secret

REDIRECT_URI = "https://www.programsinformationpeople.org/runestone/oauth"
AUTHORIZATION_URL = "https://dribbble.com/oauth/authorize"
TOKEN_URL = "https://dribbble.com/oauth/token"

def get_connection_and_cursor():
    try:
        conn = psycopg2.connect("dbname='{0}' user='{1}' password='{2}'".format(db_name, db_user, db_password))
        print('Success connecting to database')
    except:
        print('Unable to connect to database. Check server and credentials')
        sys.exit(1)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return conn, cur

# ----------------------------------------------------------------------------------
# Referencing codes from class(nytime.py)
# ----------------------------------------------------------------------------------
# Check if the cache has expired
def has_cache_expired(timestamp_str, expired_in_days = 3):
    now = datetime.now()
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)

    delta = now - cache_timestamp
    delta_in_days = delta.days

    if delta_in_days > expired_in_days:
        return True
    else:
        return False

# Add user_diction into cache
def set_in_cache(username, filename, user_dict):
    CACHE_DICTION = {}
    CACHE_DICTION[username] = {
        'userdiction' : user_dict,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
    }

    with open(filename, 'w', encoding = 'utf-8') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

# Get user_diction from the cache if cache has not expired
def get_from_cache(filename, username):
    try:
        with open(filename, 'r', encoding = 'utf-8') as cache_file:
            cache_json = cache_file.read()
            CACHE_DICTION = json.loads(cache_json)
            if username in CACHE_DICTION:
                name_dict = CACHE_DICTION[username]

                if has_cache_expired(name_dict['timestamp']):
                    del CACHE_DICTION[username]
                    name_dict = None
                else:
                    name_dict = CACHE_DICTION[username]['userdiction']
            else:
                name_dict = None
            return name_dict
    except:
        print('No cache can be found or cache has expired.')
        name_dict = None
# ----------------------------------------------------------------------------------
# Referencing codes from class(nytime.py)
# ----------------------------------------------------------------------------------



#  Get user_diction via OAuth2 from dribbble api and set the user_diction into cache file
def get_user_dict(username, filename, expired_in_days = 3):
    user_dict = get_from_cache(filename, username)
    user_url = 'https://api.dribbble.com/v1/users/{0}/shots'.format(username)
    if user_dict:
        print('Loading from cache: {0}'.format(user_url))
    else:
        print('Fetching a fresh copy: {0}'.format(user_url))
        oauth2inst = requests_oauthlib.OAuth2Session(CLIENT_KEY, redirect_uri = REDIRECT_URI) #Create an instance for an OAuth2 session

        authorization_url, state = oauth2inst.authorization_url(AUTHORIZATION_URL) 

        webbrowser.open(authorization_url) #Open the authorization url to grant permission


        authorization_response = input('Authenticate and then enter the full callback URL: ').strip()

        token = oauth2inst.fetch_token(TOKEN_URL, authorization_response=authorization_response, client_secret=CLIENT_SECRET)

        r = oauth2inst.get(user_url)
        user_dict = json.loads(r.text)
        set_in_cache(username, filename, user_dict)
    return user_dict

class Shots(object):
    def __init__(self, new_dict):
        self.url = new_dict['url']
        self.title = new_dict['title']
        self.likes = new_dict['likes']
        self.views = new_dict['views']
        self.create_time = new_dict['create_time']
        self.ratio = new_dict['ratio']
        self.id = 0

    def __repr__(self):
        return 'Shot Title: {0}, Likes Count: {1}, Views Count: {2}'.format(self.title, self.likes, self.views)

    def __contains__(self,test_string):
        return test_string in self.title

# Get like_counts and view_counts of each shots, also get the ratio of likes_count and views_count 
def get_sorted_dict_list(user_dict):
    shot_dict_list = []
    for shot in user_dict:
        new_dict = {}
        shot_url = shot['images']['hidpi']
        shot_title = shot['title']
        likes_count = shot['likes_count']
        views_count = shot['views_count']
        ratio = likes_count / views_count
        create_time = shot['created_at']
        new_dict['title'] = shot_title
        new_dict['url'] = shot_url
        new_dict['likes'] = likes_count
        new_dict['views'] = views_count
        new_dict['ratio'] = ratio
        new_dict['create_time'] = create_time
        shot_new_dict = Shots(new_dict)
        shot_dict_list.append(shot_new_dict)
    return shot_dict_list

def setup_database(conn, cur):
    print('setting up table Users, Shots.')
    cur.execute("DROP TABLE IF EXISTS Users CASCADE")
    cur.execute("CREATE TABLE IF NOT EXISTS Users(ID SERIAL PRIMARY KEY, Name VARCHAR(128) NOT NULL UNIQUE)")
    cur.execute("DROP TABLE IF EXISTS Shots")
    cur.execute("CREATE TABLE IF NOT EXISTS Shots(ID SERIAL PRIMARY KEY,Title VARCHAR(128) NOT NULL, Url VARCHAR(128) NOT NULL UNIQUE, CreateTime VARCHAR(128) NOT NULL UNIQUE, Views INTEGER, Likes INTEGER, Ratio NUMERIC, User_id INTEGER REFERENCES Users(id) NOT NULL)")
    conn.commit()
    print('Setup database complete')

# Write the data into database
def insert_users(username):
    cur.execute("""INSERT INTO Users(Name) VALUES (%s) RETURNING id """, (username,))
    print('Inserted {}'.format(username))
    conn.commit()

def insert_shots(shot_dict_list, user_id):
    for shot_dict in shot_dict_list:
        shot_dict.id = user_id
        # print(shot_dict.id)
        # print(shot_dict.title)
        # print(shot_dict.url)
        # print(shot_dict.likes)
        cur.execute("""INSERT INTO 
                    Shots(Title, Url, CreateTime, Views, Likes, Ratio, User_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id """, 
                    (shot_dict.title, shot_dict.url, shot_dict.create_time, shot_dict.views, 
                    shot_dict.likes, shot_dict.ratio, shot_dict.id))
        id = cur.fetchone()['id']
        # print('Inserted {}'.format(shot_dict.title))
        conn.commit()

def execute_query(query, numer_of_results=1):
    cur.execute(query)
    results = cur.fetchall()
    return results

# Main method to execute the methods.
conn, cur = get_connection_and_cursor()
setup_database(conn, cur)
for username in user_list:
    filename = '{0}.json'.format(username)
    user_url = 'https://api.dribbble.com/v1/users/{0}/shots'.format(username)
    shotsdict = get_user_dict(username, filename)
    new_dict = get_sorted_dict_list(shotsdict)
    # print(new_dict[1])
    insert_users(username)
    user_id = cur.fetchone()['id']
    insert_shots(new_dict, user_id)

print("Get user list from database....")
user_list = execute_query("SELECT name from Users", 5)

print("Get shots from the first user ordered by ratio of likes and views....")
u1_shots_list = execute_query("""SELECT Shots.title, Shots.url, Shots.likes, Shots.views from Shots INNER JOIN Users ON Shots.user_id = Users.id AND Users.id = 5 ORDER BY Shots.ratio DESC""", 10)
u1_best_five = u1_shots_list[:5]
# print(u1_best_five)

print("Get shots from the first user ordered by ratio of likes and views....")
u2_shots_list = execute_query("""SELECT Shots.title, Shots.url, Shots.likes, Shots.views from Shots INNER JOIN Users ON Shots.user_id = Users.id AND Users.id = 1 ORDER BY Shots.ratio DESC""", 10)
u2_best_five = u2_shots_list[:5]
# print(u2_best_five)

print("Get shots from the first user ordered by ratio of likes and views....")
u3_shots_list = execute_query("""SELECT Shots.title, Shots.url, Shots.likes, Shots.views from Shots INNER JOIN Users ON Shots.user_id = Users.id AND Users.id = 2 ORDER BY Shots.ratio DESC""", 10)
u3_best_five = u3_shots_list[:5]
# print(u3_best_five)

print("Get shots from the first user ordered by ratio of likes and views....")
u4_shots_list = execute_query("""SELECT Shots.title, Shots.url, Shots.likes, Shots.views from Shots INNER JOIN Users ON Shots.user_id = Users.id AND Users.id = 3 ORDER BY Shots.ratio DESC""", 10)
u4_best_five = u4_shots_list[:5]
# print(u4_best_five)

print("Get shots from the first user ordered by ratio of likes and views....")
u5_shots_list = execute_query("""SELECT Shots.title, Shots.url, Shots.likes, Shots.views from Shots INNER JOIN Users ON Shots.user_id = Users.id AND Users.id = 4 ORDER BY Shots.ratio DESC""", 10)
u5_best_five = u5_shots_list[:5]
# print(u5_best_five)


app = Flask(__name__)

@app.route('/dribbble')
def dribbble():
    return render_template('dribbble.html', user_list = user_list, u1_best_five=u1_best_five, u2_best_five=u2_best_five, u3_best_five=u3_best_five, u4_best_five=u4_best_five, u5_best_five=u5_best_five)

if __name__ == '__main__':
    app.run()
