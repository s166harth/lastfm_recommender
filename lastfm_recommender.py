#!/usr/bin/env python3

"""
Last.fm Offline Backup Suggester

This script fetches your Last.fm listening history over a defined period,
scores each track based on your listening habits, and recommends the top
songs for an offline backup.

SETUP:
1. Install dependencies:
   pip install -r requirements.txt

2. Get a Last.fm API Key:
   https://www.last.fm/api/account/create

3. Set environment variables:
   - For Linux/macOS:
     export LASTFM_API_KEY="your_api_key"
     export LASTFM_USERNAME="your_username"
   - For Windows:
     set LASTFM_API_KEY="your_api_key"
     set LASTFM_USERNAME="your_username"

RUNNING THE SCRIPT:
- To run it normally:
  python lastfm_recommender.py

- To run it in the background and save the output to a file (on Linux/macOS):
  nohup python lastfm_recommender.py > recommendations.log &
"""

import os
import time
from collections import defaultdict
from datetime import datetime, timedelta

import requests

# --- Configuration & Tunable Parameters ---

# Core settings
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
API_URL = "http://ws.audioscrobbler.com/2.0/"
API_USER_AGENT = "LastfmBackupSuggester/1.0"

# Algorithm parameters
TIME_PERIOD_DAYS = 5
NUM_SUGGESTIONS = 25

# Scoring weights
WEIGHTS = {
    "FREQUENCY": 1.0,
    "CONSISTENCY": 1.5,
    "ARTIST_AFFINITY": 0.5,
    "ALBUM_AFFINITY": 0.3,
}


def get_recent_tracks(api_key, user, from_uts, to_uts):
    """Fetches all recent tracks for a user within a time range."""
    page = 1
    total_pages = 1
    all_tracks = []

    print(f"Fetching data for user '{user}' from Last.fm...")

    while page <= total_pages:
        params = {
            "method": "user.getrecenttracks",
            "user": user,
            "api_key": api_key,
            "format": "json",
            "page": page,
            "limit": 200,  # Max limit per page
            "from": from_uts,
            "to": to_uts,
        }
        headers = {"User-Agent": API_USER_AGENT}

        try:
            response = requests.get(API_URL, params=params, headers=headers)
            response.raise_for_status()  # Raises an exception for 4XX/5XX errors
            data = response.json()

            if "error" in data:
                raise ConnectionError(f"Last.fm API Error: {data['message']}")

            if page == 1:
                total_pages = int(data["recenttracks"]["@attr"]["totalPages"])
                print(
                    f"Found {data['recenttracks']['@attr']['total']} scrobbles across {total_pages} pages."
                )

            all_tracks.extend(data["recenttracks"]["track"])
            page += 1

            # Be a good API citizen
            if total_pages > 1:
                time.sleep(0.2)

        except requests.RequestException as e:
            raise ConnectionError(f"Network error fetching data from Last.fm: {e}")

    return all_tracks


def process_scrobbles(tracks):
    """Processes raw track data into a clean list of listens."""
    processed_listens = []
    for track in tracks:
        # Skip "now playing" tracks
        if track.get("@attr", {}).get("nowplaying") == "true":
            continue

        try:
            song_name = track["name"]
            artist_name = track["artist"]["#text"]
            album_name = track["album"]["#text"]
            # Get the day of the listen
            listen_day = datetime.fromtimestamp(int(track["date"]["uts"])).strftime(
                "%Y-%m-%d"
            )

            if song_name and artist_name and album_name:
                processed_listens.append(
                    {
                        "song": song_name,
                        "artist": artist_name,
                        "album": album_name,
                        "day": listen_day,
                    }
                )
        except KeyError:
            # Handle cases where track data might be incomplete
            continue

    return processed_listens


def calculate_scores(listens, weights):
    """Aggregates data and scores each unique song."""
    song_play_counts = defaultdict(int)
    song_play_days = defaultdict(set)
    artist_total_plays = defaultdict(int)
    album_total_plays = defaultdict(int)

    for listen in listens:
        song_key = (listen["artist"], listen["song"])
        album_key = (listen["artist"], listen["album"])

        song_play_counts[song_key] += 1
        song_play_days[song_key].add(listen["day"])
        artist_total_plays[listen["artist"]] += 1
        album_total_plays[album_key] += 1

    song_scores = []
    for song_key, frequency in song_play_counts.items():
        artist, song = song_key
        album_key = (
            artist,
            next(
                (l["album"] for l in listens if (l["artist"], l["song"]) == song_key),
                None,
            ),
        )

        consistency = len(song_play_days[song_key])
        artist_affinity = artist_total_plays[artist]
        album_affinity = album_total_plays.get(album_key, 0)

        score = (
            (frequency * weights["FREQUENCY"])
            + (consistency * weights["CONSISTENCY"])
            + (artist_affinity * weights["ARTIST_AFFINITY"])
            + (album_affinity * weights["ALBUM_AFFINITY"])
        )

        song_scores.append({"artist": artist, "song": song, "score": round(score, 2)})

    # Sort by score, descending
    return sorted(song_scores, key=lambda x: x["score"], reverse=True)


def main():
    """Main function to orchestrate the script."""
    if not LASTFM_API_KEY or not LASTFM_USERNAME:
        print(
            "Error: LASTFM_API_KEY and LASTFM_USERNAME environment variables must be set."
        )
        print("Please follow the setup instructions in the script's docstring.")
        return

    try:
        # Define time range
        to_time = datetime.now()
        from_time = to_time - timedelta(days=TIME_PERIOD_DAYS)
        from_uts = int(from_time.timestamp())
        to_uts = int(to_time.timestamp())

        # Phase 1: Data Collection
        raw_tracks = get_recent_tracks(
            LASTFM_API_KEY, LASTFM_USERNAME, from_uts, to_uts
        )

        # Phase 2: Processing
        listens = process_scrobbles(raw_tracks)
        print(f"Successfully processed {len(listens)} completed scrobbles.\n")

        # Phase 3: Scoring & Ranking
        ranked_songs = calculate_scores(listens, WEIGHTS)

        # Phase 4: Generate Output
        print(f"--- Top {NUM_SUGGESTIONS} Song Recommendations for Offline Backup ---")
        if not ranked_songs:
            print("No listening history found for the specified period.")
            return

        for i, item in enumerate(ranked_songs[:NUM_SUGGESTIONS], 1):
            print(
                f"{i:2}. \"{item['song']}\" by {item['artist']} (Score: {item['score']})"
            )

    except (ConnectionError, ValueError) as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
