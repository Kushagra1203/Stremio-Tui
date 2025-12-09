# api/cinemeta.py
from config import CINEMETA_URL, CINEMETA_CATALOG_URL

class CinemetaMixin:
    async def get_series_details_cinemeta(self, imdb_id: str, type_: str = "series"):
        try:
            url = f"{CINEMETA_URL}/{type_}/{imdb_id}.json"
            # FIX 1: Add follow_redirects=True
            resp = await self.client.get(url, follow_redirects=True)
            if resp.status_code == 200:
                return resp.json().get('meta', {})
        except:
            pass
        return {}

    async def get_catalog_cinemeta(self, type_: str, id_: str = "top"):
        """
        Fetches a catalog (list of items).
        type_: 'movie' or 'series'
        id_: 'top' (Popular), 'imdbRating' (Top Rated)
        """
        try:
            url = f"{CINEMETA_CATALOG_URL}/{type_}/{id_}.json"
            
            # FIX 2: Add follow_redirects=True here too
            resp = await self.client.get(url, follow_redirects=True)
            
            if resp.status_code == 200:
                data = resp.json()
                metas = data.get('metas', [])
                
                results = []
                for m in metas:
                    # Cinemeta uses 'id' for the IMDB ID
                    imdb_id = m.get('id') 
                    
                    if imdb_id:
                        results.append({
                            "title": m.get('name'),
                            "year": m.get('releaseInfo', '')[:4],
                            "type": m.get('type'),
                            "id": imdb_id, 
                            "poster": m.get('poster')
                        })
                return results
            else:
                with open("debug_error.log", "a") as f:
                    f.write(f"Cinemeta HTTP Error: {resp.status_code}\n")
                    
        except Exception as e:
            with open("debug_error.log", "a") as f:
                f.write(f"Cinemeta Exception: {str(e)}\n")
            pass
        return []
