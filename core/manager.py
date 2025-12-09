# core/manager.py
from api import StremioClient
from core.cache import ImageCache

class MediaManager:
    def __init__(self):
        self.client = StremioClient()
        self.images = ImageCache()

    async def get_image(self, url):
        return await self.images.get_image(url)

    async def get_unified_metadata(self, imdb_id: str, title: str):
        # 1. Try TVMaze First (Rich Data)
        meta = await self.client.get_series_details_tvmaze(imdb_id)
        
        # 2. Fallback to TMDB (This fixes your Stranger Things issue!)
        if not meta:
            meta = await self.client.get_series_details_tmdb(imdb_id)
        
        # 3. Fallback to Search
        if not meta:
            meta = await self.client.search_tvmaze_by_name(title)

        # 4. Enrich with Cinemeta (Ratings/Country)
        cinemeta_data = await self.client.get_series_details_cinemeta(imdb_id)
        if cinemeta_data and meta:
            if cinemeta_data.get('imdbRating'):
                meta['rating'] = cinemeta_data.get('imdbRating')
            if not meta.get('genres') and cinemeta_data.get('genres'):
                meta['genres'] = cinemeta_data.get('genres')
            
            # Country Fallback (Crucial for Anime detection)
            if (not meta.get('country') or meta.get('country') == "Unknown") and cinemeta_data.get('country'):
                meta['country'] = cinemeta_data.get('country')

        return meta

    async def fetch_season_ratings(self, imdb_id, season_num):
        return await self.client.get_omdb_season_ratings(imdb_id, season_num)
        
    async def fetch_all_season_details(self, imdb_id, show_title, genres=[], country="Unknown", season_keys=[]):
        """
        Smart Fetch:
        1. Checks if Anime (via Country='Japan' or Genre='Anime')
        2. If Anime -> Uses AniList
        3. Else -> Uses TVMaze (Western)
        """
        is_anime = False
        
        # Layer 1: Country Check (Hard Confirmation)
        c_str = str(country).upper()
        if "JAPAN" in c_str or "JP" in c_str:
            is_anime = True
            
        # Layer 2: Genre Check (Soft Confirmation)
        if not is_anime and genres:
            g_str = " ".join(genres).lower()
            if "anime" in g_str: 
                is_anime = True

        # --- PATH A: ANIME (AniList) ---
        if is_anime:
            results = {}
            for s_num in season_keys:
                anilist_data = await self.client.get_anilist_season_data(show_title, s_num)
                if anilist_data:
                    results[s_num] = anilist_data
            
            # Fallback to Western logic if AniList fails completely
            if results: 
                return results

        # --- PATH B: WESTERN (TVMaze) ---
        return await self.client.get_all_seasons_details_tvmaze(imdb_id)

    async def get_streams(self, type_, id_):
        return await self.client.get_all_streams(type_, id_)

    async def search_imdb(self, query):
        return await self.client.search_imdb(query)

    async def close(self):
        await self.client.close()
