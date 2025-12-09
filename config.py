# config.py
import os

# --- API KEYS ---
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# --- URLs ---
CINEMETA_URL = "https://v3-cinemeta.strem.io/meta"
TVMAZE_URL = "https://api.tvmaze.com"
TMDB_ADDON_URL = "https://94c8cb9f702d-tmdb-addon.baby-beamup.club"
OMDB_URL = "http://www.omdbapi.com"
ANILIST_URL = "https://graphql.anilist.co"

# --- CONFIG ---
HEADERS = {
    "User-Agent": "Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

PROVIDERS = [
    {
        "name": "Torrentio",
        "url": "https://torrentio.strem.fun/qualityfilter=480p,other,scr,cam,unknown/manifest.json"
    },
    {
        "name": "Comet",
        "url": "https://comet.elfhosted.com/manifest.json" 
    }
]
