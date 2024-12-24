Project Overview

This project is a comprehensive Spotify data analysis and recommendation system. It combines data aggregation, processing, and visualization into a dashboard using Streamlit, leveraging Spotify’s API and SQL databases. The system tracks your listening history, provides insights into your habits, and generates personalized song recommendations based on your listening patterns.

Spotify Listening History Aggregation

Script
updating_spotify_db.py

Functionality
Initializes an SQLite database (spotify_listening_history.db) to store your listening history.
Uses the Spotify API to fetch recently played tracks, including metadata like: Track name, Artist name, Genres, Playback timestamp, and Duration in seconds.
Once initialized, only adds new songs listened to, using playback timestamp to avoid duplication.
Converts timestamps into EST for consistency.
Updates the database every 90 minutes automatically using the schedule library, ensuring your listening history is always up to date.

Listening History Insights and Visualization

Script
spotify_dashboard.py

Functionality
Creates an interactive dashboard with Streamlit to visualize your listening history.

Tabs:
Recently Played:
Displays the last 100 songs you’ve listened to.
Bar charts of the top 5 most-listened-to artists and genres from these songs.
Table of the top 5 most-streamed songs with playback duration.
Past 30 Days:
Highlights your top 5 songs, artists, and genres from the last month.
Includes playback duration in HH:MM:SS format for easy interpretation.
All Time:
Showcases the top 25 artists and top 50 songs of all time.
Organized by total playtime and stream counts.
Recommendations:
Displays a ranked list of recommended songs based on your listening history. (stored in spotify_recommendations.db)
Includes similarity scores (lower values mean closer matches).

Personalized Song Recommendations

Script
spotify_similarity.py

Functionality
Analyzes your top 5 most-streamed songs and artists.
Converts these songs and artists into Spotify-readable IDs.
Uses the Spotify API’s recommendations endpoint to generate a catalog of related songs.
Fetches audio features (e.g., danceability, energy, valence) for: Your top 50 songs and the recommended songs from Spotify.
Computes similarity scores using Euclidean distance to compare audio features.
Stores the recommendations in a separate database (spotify_recommendations.db), ranked by similarity.

Key Technologies

1.	Spotify API:
	•	Fetches listening history, recommendations, and audio features.
2.	Streamlit:
	•	Creates an interactive, web-based dashboard.
3.	SQLite:
	•	Stores listening history and recommendation data.
4.	Scikit-Learn:
	•	Calculates similarity scores using Euclidean distance.
5.	Plotly:
	•	Generates dynamic visualizations for the dashboard.

Future Enhancements

In the future to continue to contribute to this project, some added features I would explore include adding user input for recommendations, allowing users to enter genres from which to draw recommendations. Additionally, allowing users to see their listening data over time to identify trends for specific time periods or times of day. 
