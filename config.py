# config.py
import os

# --- API KEYS ---
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# --- URLs ---
CINEMETA_URL = "https://v3-cinemeta.strem.io/meta"
CINEMETA_CATALOG_URL = "https://v3-cinemeta.strem.io/catalog" # <--- NEW
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

# --- TORRENT TRACKERS ---
# Stremio addons such as Torrentio return a bare infoHash with no tracker
# list, so a magnet built straight from that hash has nothing to announce to
# and sits at "0 peers" forever. Stremio itself gets away with it because its
# torrent engine injects a tracker list internally; a standalone client has to
# supply its own. These are public BitTorrent trackers, passed as `tr`
# parameters on the magnet URI.
TRACKERS = [
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
    "udp://open.demonii.com:1337/announce",
    "udp://tracker.openbittorrent.com:6969/announce",
    "udp://explodie.org:6969/announce",
    "udp://tracker.dler.org:6969/announce",
    "udp://tracker1.bt.moack.co.kr:80/announce",
    "wss://tracker.openwebtorrent.com",
]
