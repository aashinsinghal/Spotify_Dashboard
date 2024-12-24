import sqlite3
import pandas as pd
import time
import schedule
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import pytz
from datetime import datetime

# Spotify API credentials
CLIENT_ID = '898e8b7eff8e4670a28053a8c4bc7103'
CLIENT_SECRET = '57c5bf7e42324941918e45a47ceed51b'
REDIRECT_URI = 'http://localhost:8888/callback'
SCOPE = 'user-read-recently-played'

DB_NAME = "spotify_listening_history.db"

# Functions for database and API operations
def initialize_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS listening_history (
            track_name TEXT,
            artist_name TEXT,
            genres TEXT,
            played_at TEXT UNIQUE,
            duration_seconds INTEGER
        )
    """)
    conn.commit()
    conn.close()

def authenticate_spotify():
    sp = Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))
    return sp

def fetch_recently_played(sp, limit=50):
    results = sp.current_user_recently_played(limit=limit)
    data = []
    for item in results['items']:
        track = item['track']
        artist_name = track['artists'][0]['name']
        artist_id = track['artists'][0]['id']
        genres = sp.artist(artist_id).get('genres', [])
        played_at_utc = item['played_at']
        duration_seconds = track['duration_ms'] // 1000

        played_at_datetime = datetime.strptime(played_at_utc, '%Y-%m-%dT%H:%M:%S.%fZ')
        utc_zone = pytz.timezone('UTC')
        est_zone = pytz.timezone('US/Eastern')
        played_at_datetime = utc_zone.localize(played_at_datetime).astimezone(est_zone)

        played_at_est = played_at_datetime.strftime('%Y-%m-%d | %H:%M:%S')
        data.append({
            'Track Name': track['name'],
            'Artist Name': artist_name,
            'Genres': ', '.join(genres),
            'Played At': played_at_est,
            'Duration Seconds': duration_seconds
        })
    return pd.DataFrame(data)

def get_latest_timestamp_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(played_at) FROM listening_history")
    result = cursor.fetchone()[0]
    conn.close()
    return result

def store_new_songs(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    new_songs_count = 0
    for _, row in data.iterrows():
        try:
            cursor.execute("""
                INSERT INTO listening_history (track_name, artist_name, genres, played_at, duration_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (row['Track Name'], row['Artist Name'], row['Genres'], row['Played At'], row['Duration Seconds']))
            new_songs_count += 1
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()
    print(f"{new_songs_count} new songs added to the database.")

def update_database():
    """
    Function to update the database with new songs from Spotify API.
    """
    print("Running database update...")
    sp = authenticate_spotify()
    recently_played_data = fetch_recently_played(sp)

    latest_timestamp = get_latest_timestamp_from_db()
    if latest_timestamp:
        recently_played_data = recently_played_data[recently_played_data['Played At'] > latest_timestamp]

    if not recently_played_data.empty:
        store_new_songs(recently_played_data)
    else:
        print("No new songs to add to the database.")

# Initialize the database
initialize_database()

# Update the database immediately on script start
print("Performing initial database update...")
update_database()

# Schedule the update every 90 minutes
schedule.every(90).minutes.do(update_database)

print("Scheduler is running. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(1)