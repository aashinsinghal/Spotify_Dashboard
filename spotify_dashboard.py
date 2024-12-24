import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# Database file path
DB_PATH = "spotify_listening_history.db"
RECOMMENDATIONS_DB = "spotify_recommendations.db"

# Utility function: Convert seconds to HH:MM:SS
def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Fetch data functions
def fetch_recently_played(limit=100):
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT * FROM listening_history ORDER BY played_at DESC LIMIT {limit}"
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data

def fetch_past_30_days():
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT artist_name AS Artist, track_name AS Song, COUNT(*) AS Streams,
               SUM(duration_seconds) AS Total_Time
        FROM listening_history
        WHERE played_at >= datetime('now', '-30 days')
        GROUP BY artist_name, track_name
        ORDER BY Streams DESC
        LIMIT 5
    """
    data = pd.read_sql_query(query, conn)
    data['Total_Time_HMS'] = data['Total_Time'].apply(seconds_to_hms)
    conn.close()
    return data

def fetch_top_artists(limit=50):
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT artist_name AS Artist, SUM(duration_seconds) AS Total_Time,
               COUNT(*) AS Streams
        FROM listening_history
        GROUP BY artist_name
        ORDER BY Total_Time DESC
        LIMIT {limit}
    """
    data = pd.read_sql_query(query, conn)
    data['Total_Time_HMS'] = data['Total_Time'].apply(seconds_to_hms)
    conn.close()
    return data

def fetch_top_songs(limit=50):
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT artist_name AS Artist, track_name AS Song, COUNT(*) AS Streams,
               SUM(duration_seconds) AS Total_Time
        FROM listening_history
        GROUP BY artist_name, track_name
        ORDER BY Streams DESC
        LIMIT {limit}
    """
    data = pd.read_sql_query(query, conn)
    data['Total_Time_HMS'] = data['Total_Time'].apply(seconds_to_hms)
    conn.close()
    return data

def fetch_top_genres(limit=5):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT genres, COUNT(*) AS Streams
        FROM listening_history
        GROUP BY genres
        ORDER BY Streams DESC
        LIMIT 5
    """
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data


def fetch_recommendations():
    """
    Fetch recommended songs from the recommendations database.
    """
    conn = sqlite3.connect(RECOMMENDATIONS_DB)
    query = """
        SELECT track_name AS Song, artist_name AS Artist, average_distance AS "Similarity"
        FROM ranked_recommendations
        ORDER BY average_distance ASC
    """
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data

# Streamlit App
st.set_page_config(page_title="Spotify Listening Dashboard", layout="wide")
st.title("Spotify Listening Dashboard")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Recently Played", "Past 30 Days", "All Time", "Recommendations"])

# Tab 1: Recently Played
with tab1:
    st.write("## Recently Played")
    # Fetch and display the last 100 songs
    recently_played = fetch_recently_played()
    st.write("### Last 100 Songs")
    st.dataframe(recently_played)
    
    # Top 5 artists in the last 100 songs
    st.write("### Top 5 Artists")
    top_5_artists = recently_played['artist_name'].value_counts().head(5).reset_index()
    top_5_artists.columns = ['Artist', 'Streams']
    fig_artists = px.bar(top_5_artists, x='Artist', y='Streams', title="Top 5 Artists (Last 100 Songs)")
    st.plotly_chart(fig_artists)
    
    # Top 5 genres in the last 100 songs
    st.write("### Top 5 Genres")
    top_5_genres = recently_played['genres'].value_counts().head(5).reset_index()
    top_5_genres.columns = ['Genre', 'Streams']
    fig_genres = px.bar(top_5_genres, x='Genre', y='Streams', title="Top 5 Genres (Last 100 Songs)")
    st.plotly_chart(fig_genres)
    
    # Top 5 most listened-to songs
    st.write("### Top 5 Songs")
    top_5_songs = recently_played.groupby(['artist_name', 'track_name']).size().reset_index(name='Streams').sort_values(by='Streams', ascending=False).head(5)
    top_5_songs['Total_Time_HMS'] = recently_played.groupby(['artist_name', 'track_name'])['duration_seconds'].sum().reset_index()['duration_seconds'].apply(seconds_to_hms)
    st.dataframe(top_5_songs.rename(columns={'artist_name': 'Artist', 'track_name': 'Song'}))

# Tab 2: Past 30 Days
with tab2:
    st.write("## Past 30 Days")
    # Top 5 songs
    st.write("### Top 5 Songs")
    past_30_days_songs = fetch_past_30_days()
    st.dataframe(past_30_days_songs.rename(columns={'Total_Time_HMS': 'Time Listened'}))
    
    # Top 5 artists
    st.write("### Top 5 Artists")
    top_artists_30_days = fetch_top_artists(limit=5)
    st.dataframe(top_artists_30_days.rename(columns={'Total_Time_HMS': 'Time Listened'}))
    
    # Top 5 genres
    st.write("### Top 5 Genres")
    top_genres_30_days = fetch_top_genres(limit=5)
    fig_genres_30_days = px.bar(top_genres_30_days, x='genres', y='Streams', title="Top 5 Genres (Past 30 Days)")
    st.plotly_chart(fig_genres_30_days)

# Tab 3: All Time
with tab3:
    st.write("## All Time")
    # Top 25 artists
    st.write("### Top 25 Artists")
    top_25_artists = fetch_top_artists(limit=25)
    st.dataframe(top_25_artists.rename(columns={'Total_Time_HMS': 'Time Listened'}))
    
    # Top 50 songs
    st.write("### Top 50 Songs")
    top_50_songs = fetch_top_songs(limit=50)
    st.dataframe(top_50_songs.rename(columns={'Total_Time_HMS': 'Time Listened'}))

with tab4:
    st.write("## Recommendations")
    st.write("Here are some recommended songs based on your listening history:")
    recommendations = fetch_recommendations()
    st.dataframe(recommendations)