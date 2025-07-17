"""
Creates (or updates) a playlist called "Playlists Tracks Not In Library" in your Tidal account.
This playlist contains all tracks that appear in any of your playlists but are NOT in your Tidal library (favorites).

Useful for finding playlist tracks you haven't actually added to your library.

If you later add or remove tracks from your library or playlists, running the script again will update the "Playlists Tracks Not In Library" playlist accordingly.
"""

import json
import os
from time import sleep
import tidalapi
from tidalapi.types import ItemOrder, OrderDirection

PLAYLIST_NAME = "Playlists Tracks Not In Library"
SESSION_FILE = "tidal_session.json"
TIDAL_API_BATCH_SIZE = 100

def save_session(session):
    data = {
        "token_type": session.token_type,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "expiry_time": session.expiry_time.timestamp(),
    }
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f)

def load_session():
    with open(SESSION_FILE, "r") as f:
        data = json.load(f)
    session = tidalapi.Session()
    session.load_oauth_session(
        data["token_type"],
        data["access_token"],
        data["refresh_token"],
        data["expiry_time"],
    )
    return session

def fetch_all_user_favorite_tracks(user, page_size=1000):
    all_tracks = []
    offset = 0
    while True:
        new_tracks = user.favorites.tracks(
            limit=page_size,
            offset=offset,
            order=ItemOrder.Date,
            order_direction=OrderDirection.Ascending
        )
        if not new_tracks:
            break
        all_tracks.extend(new_tracks)
        offset += len(new_tracks)
        sleep(0.1)
    seen_track_ids = set()
    deduped_tracks = []
    for track in all_tracks:
        track_id = getattr(track, "id", None)
        if track_id is not None and track_id not in seen_track_ids:
            seen_track_ids.add(track_id)
            deduped_tracks.append(track)
    return deduped_tracks

def main():
    session = tidalapi.Session()
    if os.path.exists(SESSION_FILE):
        try:
            session = load_session()
            if session.check_login():
                print("✅ Loaded saved credentials.")
            else:
                raise Exception("Session expired.")
        except Exception as e:
            print("❌ Session load failed:", e)
            os.remove(SESSION_FILE)
            session.login_oauth_simple(fn_print=print)
            save_session(session)
            print("Session re-saved.")
    else:
        session.login_oauth_simple(fn_print=print)
        save_session(session)
        print("✅ Session saved after login.")
    user = session.user
    print(f"Logged in as {getattr(user, 'name', user.username)} ({user.username})")

    # --- Gather tracks in all playlists ---
    playlists = list(user.playlists())
    print(f"Found {len(playlists)} playlists.")
    playlist_tracks = set()
    target_playlist = None

    for pl in playlists:
        if pl.name == PLAYLIST_NAME:
            target_playlist = pl
            continue
        for track in pl.tracks():
            playlist_tracks.add(track.id)
    print(f"Total unique tracks found in playlists: {len(playlist_tracks)}")

    favorites = fetch_all_user_favorite_tracks(user)
    favorite_ids = {t.id for t in favorites}
    print(f"Found {len(favorites)} favorite tracks in your Tidal library.")

    # --- Tracks in playlists but NOT in favorites ---
    tracks_to_add_ids = playlist_tracks - favorite_ids
    print(f"{len(tracks_to_add_ids)} tracks are in playlists but NOT in library.")

    id_to_track = {}
    for pl in playlists:
        if pl.name == PLAYLIST_NAME:
            continue
        for track in pl.tracks():
            if track.id in tracks_to_add_ids:
                id_to_track[track.id] = track
    tracks_to_add = [id_to_track[tid] for tid in tracks_to_add_ids]

    # --- Create or Update Target Playlist ---
    if target_playlist:
        print(f"Updating existing playlist: '{PLAYLIST_NAME}'")
        current = list(target_playlist.tracks())
        current_ids = {t.id for t in current}

        # Tracks that should be removed (now in library)
        should_remove = [t for t in current if t.id in favorite_ids]
        # Tracks to add (in playlists but not yet in playlist or in library)
        should_add = [t for t in tracks_to_add if t.id not in current_ids]

        if should_remove:
            print(f"Removing {len(should_remove)} tracks now in library...")
            for t in should_remove:
                target_playlist.remove_by_id(t.id)

        if should_add:
            print(f"Adding {len(should_add)} tracks not in library...")
            for i in range(0, len(should_add), TIDAL_API_BATCH_SIZE):
                batch = should_add[i:i+TIDAL_API_BATCH_SIZE]
                target_playlist.add([t.id for t in batch])

        if not should_remove and not should_add:
            print("No tracks to add or remove from target playlist.")

    else:
        print(f"Creating playlist '{PLAYLIST_NAME}' with {len(tracks_to_add)} tracks")
        target_playlist = user.create_playlist(PLAYLIST_NAME, "Tracks from all playlists not in Tidal library.")
        for i in range(0, len(tracks_to_add), TIDAL_API_BATCH_SIZE):
            batch = tracks_to_add[i:i+TIDAL_API_BATCH_SIZE]
            target_playlist.add([t.id for t in batch])

    print(f"✅ '{PLAYLIST_NAME}' updated: {len(tracks_to_add)} tracks not in library.")

if __name__ == "__main__":
    main()
