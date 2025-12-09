# api/cinemeta.py
from config import CINEMETA_URL

class CinemetaMixin:
    async def get_series_details_cinemeta(self, imdb_id: str, type_: str = "series"):
        try:
            url = f"{CINEMETA_URL}/{type_}/{imdb_id}.json"
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return resp.json().get('meta', {})
        except:
            pass
        return {}
