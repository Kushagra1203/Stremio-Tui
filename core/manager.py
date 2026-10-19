# core/manager.py
from api import StremioClient

from core.cache import ImageCache
from core.history import HistoryManager


class MediaManager:
    def __init__(self):
        self.client = StremioClient()
        self.images = ImageCache()
        self.history = HistoryManager()

    def add_to_history(self, data):
        self.history.add_entry(data)

    def get_history(self):
        return self.history.get_sorted_history()

    async def get_trending(self, type_="series"):
        return await self.client.get_catalog_cinemeta(type_, "top")

    async def get_image(self, url):
        return await self.images.get_image(url)

    async def get_unified_metadata(self, imdb_id: str, title: str):
        # 1. Get rich metadata (TVMaze/TMDB) - This preserves your original "poster logic"
        meta = await self.client.get_series_details_tvmaze(imdb_id)
        if not meta:
            meta = await self.client.get_series_details_tmdb(imdb_id)
        if not meta:
            meta = await self.client.search_tvmaze_by_name(title)

        # 2. Get Cinemeta for the full season structure (ensures JJK seasons 2 & 3 appear)
        cinemeta_data = await self.client.get_series_details_cinemeta(imdb_id)

        if cinemeta_data:
            if not meta:
                meta = cinemeta_data
                # Fix missing 'episode' key in raw Cinemeta data
                for v in meta.get("videos", []):
                    if "number" in v:
                        v["episode"] = v["number"]
            else:
                # Merge: Use Cinemeta for the list, but fill with TVMaze/TMDB metadata
                c_videos = cinemeta_data.get("videos", [])
                m_videos = meta.get("videos", [])

                # Map rich videos by (season, episode) for quick lookup
                rich_map = {
                    (v.get("season"), v.get("episode")): v
                    for v in m_videos
                    if v.get("season") is not None
                }

                merged_videos = []
                for cv in c_videos:
                    s = cv.get("season")
                    e = cv.get("number")  # Cinemeta uses 'number' for episode

                    if s is None or e is None:
                        continue

                    # Ensure the UI can see the episode number
                    cv["episode"] = e

                    # Inject rich metadata (thumbnails/descriptions) if available
                    rich_ep = rich_map.get((int(s), int(e)))
                    if rich_ep:
                        cv["thumbnail"] = rich_ep.get("thumbnail") or cv.get(
                            "thumbnail"
                        )
                        cv["overview"] = rich_ep.get("overview") or cv.get("overview")
                        cv["name"] = rich_ep.get("name") or cv.get("name")
                        cv["rating"] = rich_ep.get("rating") or cv.get("rating")

                    merged_videos.append(cv)

                meta["videos"] = merged_videos

                # Enrich core show fields from Cinemeta
                if cinemeta_data.get("imdbRating"):
                    meta["rating"] = cinemeta_data.get("imdbRating")
                if not meta.get("genres"):
                    meta["genres"] = cinemeta_data.get("genres", [])
                if not meta.get("country") or meta.get("country") == "Unknown":
                    meta["country"] = cinemeta_data.get("country", "Unknown")

        return meta

    async def fetch_season_ratings(self, imdb_id, season_num):
        return await self.client.get_omdb_season_ratings(imdb_id, season_num)

    async def fetch_all_season_details(
        self, imdb_id, show_title, genres=[], country="Unknown", season_keys=[]
    ):
        is_anime = False
        c_str = str(country).upper()
        if "JAPAN" in c_str or "JP" in c_str:
            is_anime = True

        if not is_anime and genres:
            g_str = " ".join(genres).lower()
            if "anime" in g_str:
                is_anime = True

        if is_anime:
            results = {}
            for s_num in season_keys:
                anilist_data = await self.client.get_anilist_season_data(
                    show_title, s_num
                )
                if anilist_data:
                    results[s_num] = anilist_data
            if results:
                return results

        return await self.client.get_all_seasons_details_tvmaze(imdb_id)

    async def get_streams(self, type_, id_):
        return await self.client.get_all_streams(type_, id_)

    async def search_imdb(self, query):
        return await self.client.search_imdb(query)

    async def close(self):
        await self.client.close()
