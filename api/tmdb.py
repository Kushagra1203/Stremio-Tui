# api/tmdb.py
from config import TMDB_ADDON_URL

class TMDBMixin:
    async def get_series_details_tmdb(self, imdb_id: str, type_: str = "series"):
        try:
            url = f"{TMDB_ADDON_URL}/meta/{type_}/{imdb_id}.json"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                data = resp.json().get('meta', {})
                if not data: return None
                
                # Extract Country Safely
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
                    "country": country,
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
