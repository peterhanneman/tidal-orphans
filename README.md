# Tidal Orphans

Was frustrated with Tidal's lack of library management capabilities so I created a set of Python scripts to manage and analyze Tidal playlists and library to find orphaned tracks.

Built using the [tidalapi](https://github.com/tamland/python-tidal) Python library.

## Script Summaries
#### favorites_not_in_playlists.py

Creates (or updates) a playlist called "Favorites Not In Playlists" in your Tidal account.
This playlist contains all tracks that are in your Tidal library (favorites) but not included in any of your playlists.

Useful for finding forgotten library tracks.

If you later add or remove tracks from your library or playlists, running the script again will update the "Favorites Not In Playlists" playlist accordingly.


#### playlist_tracks_not_in_favorites.py

Creates (or updates) a playlist called "Playlist Tracks Not In Favorites" in your Tidal account.
This playlist contains all tracks that appear in any of your playlists but are NOT in your Tidal library (favorites).

Useful for finding playlist tracks you haven't actually added to your library.

If you later add or remove tracks from your library or playlists, running the script again will update the "Playlist Tracks Not In Favorites" playlist accordingly.

---

## Setup Instructions

### 1. Clone or Download the Project

Download or clone this repository to your local machine.

### 2. Python Environment

Recommended to use a virtual environment.

#### Using `venv` (Standard Python):

```bash
python3 -m venv tidal-orphans
source tidal-orphans/bin/activate
# On Windows: tidal-orphans\Scripts\activate
```

#### Using `virtualenvwrapper`:
```bash
mkvirtualenv tidal-orphans
workon tidal-orphans
```

#### Using Conda:
```bash
conda create -n tidal-orphans
conda activate tidal-orphans
```

### 3. Install Required Packages

#### Using `pip`:
```bash
pip install tidalapi
```

#### Using Conda:
```bash
conda install pip
pip install tidalapi
```

### 4. Tidal Authentication

The first time you run either script, you will be prompted to complete a Tidal OAuth authentication flow in your browser.
After initial setup, your session will be reused (stored in tidal_session.json).  Sessions expire after 24 hours and will need to be re-authenticated.


## Troubleshooting

If authentication fails, delete tidal_session.json and re-run the script to perform a fresh login.

You may need to update tidalapi occasionally to maintain compatibility with Tidal API changes.

```bash
pip install --upgrade tidalapi
```


## License

This project is provided as-is under the MIT License.