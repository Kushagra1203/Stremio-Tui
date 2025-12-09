# controllers.py
from core import get_poster_image
import asyncio

class SeriesController:
    def __init__(self, client):
        self.client = client
        self.image_cache = {}

    async def get_unified_metadata(self, imdb_id: str, title: str):
        # 1. Try TVMaze First (Rich Data)
        meta = await self.client.get_series_details_tvmaze(imdb_id)
        
        # 2. Fallback to TMDB
        if not meta:
            meta = await self.client.get_series_details_tmdb(imdb_id)
        
        # 3. Fallback to Search
        if not meta:
            meta = await self.client.search_tvmaze_by_name(title)

        # 4. Enrich with Cinemeta (Great for Ratings & Genres & Country)
        cinemeta_data = await self.client.get_series_details_cinemeta(imdb_id)
        if cinemeta_data and meta:
            if cinemeta_data.get('imdbRating'):
                meta['rating'] = cinemeta_data.get('imdbRating')
            if not meta.get('genres') and cinemeta_data.get('genres'):
                meta['genres'] = cinemeta_data.get('genres')
            
            # --- CRITICAL: PULL COUNTRY FROM CINEMETA IF MISSING ---
            if (not meta.get('country') or meta.get('country') == "Unknown") and cinemeta_data.get('country'):
                meta['country'] = cinemeta_data.get('country')

        return meta

    async def fetch_season_ratings(self, imdb_id, season_num):
        return await self.client.get_omdb_season_ratings(imdb_id, season_num)
        
    async def fetch_all_season_details(self, imdb_id, show_title, genres=[], country="Unknown", season_keys=[]):
        """
        Smart Fetch Strategy:
        1. COUNTRY CHECK: If 'Japan' or 'JP' -> Anime Mode (AniList).
        2. GENRE CHECK: If 'Anime' in genres -> Anime Mode.
        3. DEFAULT: Western Mode (TVMaze).
        """
        is_anime = False
        
        # 1. Layer 1: Country Check (Hard Confirmation)
        c_str = str(country).upper()
        if "JAPAN" in c_str or "JP" in c_str:
            is_anime = True
            print(f"[CONTROLLER] 🎌 Detected Country '{country}' -> Switching to Anime Mode.")

        # 2. Layer 2: Genre Check (Soft Confirmation)
        if not is_anime and genres:
            g_str = " ".join(genres).lower()
            if "anime" in g_str: 
                is_anime = True
                print(f"[CONTROLLER] 🎌 Detected Genre 'Anime' -> Switching to Anime Mode.")

        # --- PATH A: ANIME (AniList) ---
        if is_anime:
            results = {}
            for s_num in season_keys:
                anilist_data = await self.client.get_anilist_season_data(show_title, s_num)
                if anilist_data:
                    results[s_num] = anilist_data
            
            if results:
                return results
            
            print("[CONTROLLER] ⚠️ AniList failed. Fallback to TVMaze.")

        # --- PATH B: WESTERN (TVMaze) ---
        return await self.client.get_all_seasons_details_tvmaze(imdb_id)

    async def get_image(self, url):
        if not url: return None
        if url in self.image_cache:
            return self.image_cache[url]
            
        pil_image = await get_poster_image(url)
        if pil_image:
            self.image_cache[url] = pil_image
            return pil_image
        return None
