# core.py
import os
import httpx
import asyncio
import urllib.parse
from datetime import datetime
from io import BytesIO
from PIL import Image

# --- CONFIGURATION ---
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

if not OMDB_API_KEY:
    print("\n[CORE] ❌ OMDb API Key NOT FOUND in environment variables!")

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

# URLs
CINEMETA_URL = "https://v3-cinemeta.strem.io/meta"
TVMAZE_URL = "https://api.tvmaze.com"
TMDB_ADDON_URL = "https://94c8cb9f702d-tmdb-addon.baby-beamup.club"
OMDB_URL = "http://www.omdbapi.com"
ANILIST_URL = "https://graphql.anilist.co"

HEADERS = {
    "User-Agent": "Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# --- HELPERS ---
def format_size(size_bytes):
    if not size_bytes: return ""
    try:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f}{unit}"
            size /= 1024
    except:
        return ""
    return ""

def get_magnet_name(magnet_link):
    try:
        parsed = urllib.parse.urlparse(magnet_link)
        params = urllib.parse.parse_qs(parsed.query)
        if 'dn' in params:
            return params['dn'][0].replace('.', ' ')
    except:
        pass
    return "Unknown Release"

def format_date(date_str):
    if not date_str: return "N/A"
    try:
        if 'T' in str(date_str):
            date_str = str(date_str).split('T')[0]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except:
        return date_str

# --- IMAGE PROCESSING ---
async def get_poster_image(url):
    """Downloads an image and returns a PIL Image object."""
    if not url: return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=4.0)
            if resp.status_code == 200:
                return Image.open(BytesIO(resp.content))
    except:
        pass
    return None

# --- API CLIENT ---
class StremioClient:
    def __init__(self):
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=15.0)

    async def search_imdb(self, query: str):
        url = f"https://v3.sg.media-imdb.com/suggestion/x/{query}.json"
        try:
            resp = await self.client.get(url)
            data = resp.json()
            results = []
            for item in data.get('d', []):
                if item.get('q') in ['feature', 'TV series']:
                    results.append({
                        "title": item.get('l'),
                        "year": item.get('y'),
                        "type": item.get('q'),
                        "id": item.get('id'),
                        "poster": item.get('i', {}).get('imageUrl')
                    })
            return results
        except Exception:
            return []

    async def get_series_details_tvmaze(self, imdb_id: str):
        try:
            lookup_url = f"{TVMAZE_URL}/lookup/shows?imdb={imdb_id}"
            resp = await self.client.get(lookup_url, follow_redirects=True)
            if resp.status_code != 200: return None
            
            show_data = resp.json()
            return await self._normalize_tvmaze(show_data)
        except:
            return None
    
    async def get_all_seasons_details_tvmaze(self, imdb_id):
        """
        Fetches ALL seasons for a show via TVMaze (Western/Default path).
        """
        try:
            lookup_url = f"{TVMAZE_URL}/lookup/shows?imdb={imdb_id}"
            resp = await self.client.get(lookup_url, follow_redirects=True)
            if resp.status_code != 200: return {}
            
            show_id = resp.json().get('id')
            seasons_url = f"{TVMAZE_URL}/shows/{show_id}/seasons"
            resp = await self.client.get(seasons_url)
            if resp.status_code != 200: return {}
            
            results = {}
            for s in resp.json():
                s_num = s.get('number')
                if s_num:
                    try:
                        results[int(s_num)] = {
                            "poster": s.get('image', {}).get('original'),
                            "overview": s.get('summary', '').replace('<p>', '').replace('</p>', '').replace('<b>', '').replace('</b>', ''),
                            "rating": None 
                        }
                    except: pass
            return results
        except:
            pass
        return {}
    
    # --- ANILIST LOGIC ---
    async def get_anilist_season_data(self, title, season_num):
        """
        Uses GraphQL to fuzzy search. 
        Tries "Title Season N" first, then "Title" if Season 1.
        """
        query = """
        query ($search: String) {
          Media (search: $search, type: ANIME, sort: SEARCH_MATCH) {
            description
            averageScore
            coverImage {
              extraLarge
            }
          }
        }
        """

        # Strategy: Search 'Title Season X'
        search_terms = []
        if season_num > 1:
            search_terms.append(f"{title} Season {season_num}")
            search_terms.append(f"{title} {season_num}")
        else:
            search_terms.append(f"{title}")
        
        for term in search_terms:
            try:
                resp = await self.client.post(
                    ANILIST_URL, 
                    json={'query': query, 'variables': {'search': term}}
                )
                
                if resp.status_code == 200:
                    data = resp.json().get('data', {}).get('Media')
                    if data:
                        desc = data.get('description', '')
                        if desc:
                            desc = desc.replace('<br>', '\n').replace('<i>', '').replace('</i>', '')
                        
                        score = data.get('averageScore')
                        if score: score = score / 10.0

                        return {
                            "poster": data.get('coverImage', {}).get('extraLarge'),
                            "overview": desc,
                            "rating": score 
                        }
            except:
                pass
        
        return None
    # --------------------------

    async def search_tvmaze_by_name(self, name: str):
        try:
            clean_name = name.split('(')[0].strip()
            search_url = f"{TVMAZE_URL}/search/shows?q={clean_name}"
            resp = await self.client.get(search_url)
            if resp.status_code != 200: return None
            
            results = resp.json()
            if not results: return None
            return await self._normalize_tvmaze(results[0]['show'])
        except:
            return None

    async def _fetch_tvmaze_episodes(self, tvmaze_id):
        try:
            url = f"{TVMAZE_URL}/shows/{tvmaze_id}/episodes"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return []

    async def _normalize_tvmaze(self, show_data):
        episodes = await self._fetch_tvmaze_episodes(show_data.get('id'))
        
        # 1. Extract Country safely
        country = "Unknown"
        try:
            country = show_data.get('network', {}).get('country', {}).get('name')
            if not country:
                country = show_data.get('webChannel', {}).get('country', {}).get('name')
        except:
            pass

        meta = {
            "source": "TVMaze",
            "name": show_data.get('name'),
            "description": show_data.get('summary', '').replace('<p>', '').replace('</p>', '').replace('<b>', '').replace('</b>', ''),
            "poster": show_data.get('image', {}).get('original'),
            "year": show_data.get('premiered', '')[:4] if show_data.get('premiered') else 'N/A',
            "status": show_data.get('status'),
            "runtime": show_data.get('averageRuntime'),
            "rating": show_data.get('rating', {}).get('average'),
            "genres": show_data.get('genres', []),
            "country": country, # <--- NEW
            "videos": []
        }
        for ep in episodes:
            meta['videos'].append({
                "season": ep.get('season'),
                "episode": ep.get('number'),
                "name": ep.get('name'),
                "overview": ep.get('summary', '').replace('<p>', '').replace('</p>', '').replace('<b>', '').replace('</b>', '') if ep.get('summary') else None,
                "released": ep.get('airdate'),
                "rating": ep.get('rating', {}).get('average'),
                "thumbnail": ep.get('image', {}).get('original'),
                "id": ep.get('id')
            })
        return meta

    async def get_series_details_tmdb(self, imdb_id: str, type_: str = "series"):
        try:
            url = f"{TMDB_ADDON_URL}/meta/{type_}/{imdb_id}.json"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json().get('meta', {})
                if not data: return None
                
                # 2. Extract Country Safely from TMDB
                country = "Unknown"
                if data.get('country'):
                    country = data.get('country')
                elif data.get('origin_country'):
                    if isinstance(data.get('origin_country'), list):
                        country = ",".join(data.get('origin_country'))
                    else:
                        country = str(data.get('origin_country'))

                meta = {
                    "source": "TMDB",
                    "name": data.get('name'),
                    "description": data.get('description'),
                    "poster": data.get('poster'),
                    "year": data.get('year'),
                    "status": data.get('releaseInfo', 'N/A'),
                    "runtime": data.get('runtime'),
                    "rating": data.get('imdbRating'), 
                    "genres": data.get('genres', []),
                    "country": country, # <--- NEW
                    "videos": []
                }
                for vid in data.get('videos', []):
                    meta['videos'].append({
                        "season": vid.get('season'),
                        "episode": vid.get('episode'),
                        "name": vid.get('name') or f"Episode {vid.get('episode')}",
                        "overview": vid.get('description'),
                        "released": vid.get('released'),
                        "rating": vid.get('imdbRating') or "N/A", 
                        "thumbnail": vid.get('thumbnail'),
                        "id": vid.get('id')
                    })
                return meta
        except:
            pass
        return None

    async def get_series_details_cinemeta(self, imdb_id: str, type_: str = "series"):
        try:
            url = f"{CINEMETA_URL}/{type_}/{imdb_id}.json"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return resp.json().get('meta', {})
        except:
            pass
        return {}

    # --- OMDB FETCHING ---
    async def get_omdb_season_ratings(self, imdb_id, season_num):
        """Fetches ratings for ALL episodes in a season from OMDb."""
        if not OMDB_API_KEY or OMDB_API_KEY == "YOUR_KEY_HERE":
            return {}
            
        try:
            url = f"{OMDB_URL}/?apikey={OMDB_API_KEY}&i={imdb_id}&Season={season_num}"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                ratings = {}
                for ep in data.get('Episodes', []):
                    try:
                        e_num = int(ep['Episode'])
                        rating = ep['imdbRating']
                        if rating != "N/A":
                            ratings[e_num] = rating
                    except:
                        pass
                return ratings
        except:
            pass
        return {}

    async def fetch_provider_stream(self, provider, type_, id_):
        streams = []
        status_code = None
        error_message = None
        url = None

        try:
            parsed_url = urllib.parse.urlparse(provider['url'])
            base_url_path = parsed_url.path.replace("/manifest.json", "")
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{base_url_path}"
            
            url = f"{base_url}/stream/{type_}/{id_}.json"
            
            resp = await self.client.get(url)
            status_code = resp.status_code
            
            if resp.status_code == 200:
                data = resp.json()
                streams = data.get('streams', [])
            else:
                error_message = f"HTTP Error {status_code}"
                
        except Exception as e:
            error_message = f"Network Error: {type(e).__name__}"
        
        return {
            "name": provider['name'],
            "streams": streams,
            "status": status_code,
            "error": error_message,
        }

    async def get_all_streams(self, type_: str, id_: str):
        tasks = [self.fetch_provider_stream(p, type_, id_) for p in PROVIDERS]
        results_list = await asyncio.gather(*tasks)
        
        all_streams = []
        for result in results_list:
            if result and result.get('streams'):
                all_streams.extend(result['streams'])

        return all_streams

    async def close(self):
        await self.client.aclose()
