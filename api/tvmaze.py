# api/tvmaze.py
from config import TVMAZE_URL

class TVMazeMixin:
    """
    Contains all logic for communicating with TVMaze.
    Expects 'self.client' to be an httpx.AsyncClient.
    """
    
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
            return {}

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
            "country": country,
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
