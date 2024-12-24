import sqlite3
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials
CLIENT_ID = '898e8b7eff8e4670a28053a8c4bc7103'  # Replace with your Client ID
CLIENT_SECRET = '57c5bf7e42324941918e45a47ceed51b'  # Replace with your Client Secret
REDIRECT_URI = 'http://localhost:8888/callback'  # Same as set in Spotify Dashboard
SCOPE = 'user-read-recently-played'

# Database file
DB_PATH = "spotify_listening_history.db"
RECOMMENDATIONS_DB = "spotify_recommendations.db"

# Step 1: Authenticate Spotify API
def authenticate_spotify():
    return Spotify(auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    ))

# Step 2: Fetch top songs and artists
def fetch_top_songs_and_artists():
    conn = sqlite3.connect(DB_PATH)
    top_songs_query = """
        SELECT track_name, COUNT(*) as play_count
        FROM listening_history
        GROUP BY track_name
        ORDER BY play_count DESC
        LIMIT 5
    """
    top_artists_query = """
        SELECT artist_name, COUNT(*) as play_count
        FROM listening_history
        GROUP BY artist_name
        ORDER BY play_count DESC
        LIMIT 5
    """
    top_songs = pd.read_sql_query(top_songs_query, conn)
    top_artists = pd.read_sql_query(top_artists_query, conn)
    conn.close()

    return top_songs, top_artists

# Step 3: Convert songs to Spotify track IDs
def fetch_track_ids(sp, song_names):
    track_ids = []
    for name in song_names:
        try:
            results = sp.search(q=f'track:{name}', type='track', limit=1)
            if results['tracks']['items']:
                track_ids.append(results['tracks']['items'][0]['id'])
        except Exception as e:
            print(f"Error fetching ID for song {name}: {e}")
    return track_ids

# Step 4: Convert artists to Spotify artist IDs
def fetch_artist_ids(sp, artist_names):
    artist_ids = []
    for name in artist_names:
        try:
            results = sp.search(q=f'artist:{name}', type='artist', limit=1)
            if results['artists']['items']:
                artist_ids.append(results['artists']['items'][0]['id'])
        except Exception as e:
            print(f"Error fetching ID for artist {name}: {e}")
    return artist_ids

# Step 5: Fetch recommendations
def fetch_recommendations(sp, seed_artists, seed_tracks, limit=50):
    try:
        recommendations = sp.recommendations(seed_artists=seed_artists, seed_tracks=seed_tracks, limit=limit)
        catalog = []
        for track in recommendations['tracks']:
            catalog.append({
                'Track Name': track['name'],
                'Artist': ', '.join([artist['name'] for artist in track['artists']]),
                'Track ID': track['id']
            })
        return pd.DataFrame(catalog)
    except Exception as e:
        print(f"Error fetching recommendations: {e}")
        return pd.DataFrame()

# Step 6: Fetch audio features
def fetch_audio_features(sp, track_ids):
    features = []
    for i in range(0, len(track_ids), 100):  # Spotify API accepts up to 100 IDs per request
        batch = track_ids[i:i + 100]
        response = sp.audio_features(batch)
        for feature in response:
            if feature:
                features.append({
                    'Track ID': feature['id'],
                    'Danceability': feature['danceability'],
                    'Energy': feature['energy'],
                    'Valence': feature['valence'],
                    'Tempo': feature['tempo'],
                    'Liveness': feature['liveness']
                })
    return pd.DataFrame(features)

# Step 7: Compute similarity
def compute_similarity(recent_features, catalog_features):
    feature_columns = ['Danceability', 'Energy', 'Valence', 'Tempo', 'Liveness']
    recommendations = []

    for _, catalog_song in catalog_features.iterrows():
        catalog_vector = catalog_song[feature_columns].values.reshape(1, -1)
        recent_vectors = recent_features[feature_columns].values
        distances = euclidean_distances(recent_vectors, catalog_vector).flatten()
        avg_distance = distances.mean()
        recommendations.append({
            'Track Name': catalog_song['Track Name'],
            'Artist': catalog_song['Artist'],
            'Average Distance': avg_distance
        })

    recommendations_df = pd.DataFrame(recommendations)
    return recommendations_df.sort_values(by='Average Distance')

# Step 8: Save recommendations to database
def save_to_database(df, db_name, table_name):
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    print(f"Saved recommendations to {db_name} in table '{table_name}'.")

# Main function
def main():
    sp = authenticate_spotify()

    # Fetch top songs and artists
    top_songs, top_artists = fetch_top_songs_and_artists()
    print(f"Top Songs:\n{top_songs}")
    print(f"Top Artists:\n{top_artists}")

    # Convert top songs and artists to IDs
    top_song_ids = fetch_track_ids(sp, top_songs['track_name'].tolist())
    print(f"Top Song IDs: {top_song_ids}")

    top_artist_ids = fetch_artist_ids(sp, top_artists['artist_name'].tolist())
    print(f"Top Artist IDs: {top_artist_ids}")

    # Fetch recommendations using top songs and artists as seeds
    recommendations = fetch_recommendations(sp, seed_artists=top_artist_ids, seed_tracks=top_song_ids, limit=50)
    print(f"Fetched {len(recommendations)} recommendations.")

    # Fetch audio features for top 50 songs and recommended songs
    top_50_query = """
        SELECT track_id
        FROM listening_history
        GROUP BY track_id
        ORDER BY COUNT(*) DESC
        LIMIT 50
    """
    conn = sqlite3.connect(DB_PATH)
    top_50_tracks = pd.read_sql_query(top_50_query, conn)['track_id'].tolist()
    conn.close()

    top_50_features = fetch_audio_features(sp, top_50_tracks)
    recommendations_features = fetch_audio_features(sp, recommendations['Track ID'].tolist())
    print("Fetched audio features for both top 50 songs and recommendations.")

    # Compute similarity
    ranked_recommendations = compute_similarity(top_50_features, recommendations_features)
    print("Ranked recommendations based on similarity.")

    # Save ranked recommendations to a new SQLite database
    save_to_database(ranked_recommendations, RECOMMENDATIONS_DB, 'ranked_recommendations')

if __name__ == "__main__":
    main()