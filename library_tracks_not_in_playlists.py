
import json
import os
from time import sleep
import tidalapi
from tidalapi.types import ItemOrder, OrderDirection

ORPHAN_PLAYLIST_NAME = "Orphaned Tracks"
SESSION_FILE = "tidal_session.json"
TIDAL_API_BATCH_SIZE = 100

def save_session(session):
    data = {
        "token_type": session.token_type,
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        # expiry_time is a datetime; store as timestamp
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
    """
    Fetch all favorite tracks for a Tidal user, regardless of how many there are.
    Deduplicate tracks by ID only after fetching all pages.
    """
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
    display_name = getattr(user, "name", user.username)
    print(f"Logged in as {display_name} ({user.username})")

    playlists = list(user.playlists())
    print(f"Found {len(playlists)} playlists.")

    tracks_in_playlists = set()
    orphan_playlist = None

    for pl in playlists:
        if pl.name == ORPHAN_PLAYLIST_NAME:
            orphan_playlist = pl
            continue
        for track in pl.tracks():
            tracks_in_playlists.add(track.id)

    favorites = fetch_all_user_favorite_tracks(user)
    print(f"Found {len(favorites)} favorite tracks in your Tidal library.")

    # --- Tracks in favorites but NOT in any other playlists ---
    orphan_tracks = [t for t in favorites if t.id not in tracks_in_playlists]
    print(f"{len(orphan_tracks)} tracks are NOT in any other playlists.")

    # --- Create or Update Target Playlist ---
    if orphan_playlist:
        print(f"Updating existing playlist: '{ORPHAN_PLAYLIST_NAME}'")
        current = list(orphan_playlist.tracks())
        current_ids = {t.id for t in current}

        # Tracks in orphans playlist that have since been added to another playlist
        should_remove = [t for t in current if t.id in tracks_in_playlists]
        # Orphan tracks that are missing from the existing orphans playlist (newly orphaned since last script execution)
        should_add = [t for t in orphan_tracks if t.id not in current_ids]

        if should_remove:
            print(f"Removing {len(should_remove)} tracks...")  
            for t in should_remove:
                orphan_playlist.remove_by_id(t.id)

        if should_add:
            print(f"Adding {len(should_add)} new orphan tracks...")
            for i in range(0, len(should_add), TIDAL_API_BATCH_SIZE):
                batch = should_add[i:i+TIDAL_API_BATCH_SIZE]
                orphan_playlist.add([t.id for t in batch])
        
        if not should_remove and not should_add:
            print("No tracks to add or remove from orphans playlist.")

    else:
        print(f"Creating playlist '{ORPHAN_PLAYLIST_NAME}' with {len(orphan_tracks)} tracks")
        orphan_playlist = user.create_playlist(ORPHAN_PLAYLIST_NAME, "Tracks from library not in any other playlists.")
        for i in range(0, len(orphan_tracks), TIDAL_API_BATCH_SIZE):
            batch = orphan_tracks[i:i+TIDAL_API_BATCH_SIZE]
            orphan_playlist.add([t.id for t in batch])

    print(f"✅ '{ORPHAN_PLAYLIST_NAME}' updated: {len(orphan_tracks)} orphans, {len([t for t in favorites if t.id in tracks_in_playlists])} in playlists.")

if __name__ == "__main__":
    main()
