# api/omdb.py
from config import OMDB_URL, OMDB_API_KEY

class OMDbMixin:
    async def get_omdb_season_ratings(self, imdb_id, season_num):
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
