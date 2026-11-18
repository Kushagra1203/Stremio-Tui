# core/manager.py
from api import StremioClient

from core.cache import ImageCache
from core.history import HistoryManager


def merge_series_metadata(meta, cinemeta_data):
    """Merge rich episode metadata with Cinemeta's authoritative season list.

    The two sources disagree about what a show *is*:

    * Cinemeta has the correct season/episode structure (it is the catalogue the
      player is driven from) but thin per-episode text.
    * TVMaze/TMDB have good thumbnails, summaries and names, but their season
      lists drift, especially for long-running anime.

    So Cinemeta decides *which* episodes exist, and the rich source decides
    *what they say*. Episodes are matched on ``(season, episode)``; anything the
    rich source does not cover keeps its Cinemeta values.

    This is a pure function on purpose: the merge rules are the part worth
    testing, and keeping them free of HTTP means they can be tested without
    mocking a client. Neither argument is mutated.
    """
    if not cinemeta_data:
        return meta

    if not meta:
        # No rich source at all: Cinemeta alone, with its "number" field exposed
        # as "episode" so the rest of the app only has to know one name.
        merged = dict(cinemeta_data)
        videos = []
        for video in merged.get("videos", []):
            video = dict(video)
            if "number" in video:
                video["episode"] = video["number"]
            videos.append(video)
        merged["videos"] = videos
        return merged

    merged = dict(meta)

    rich_by_episode = {}
    for video in meta.get("videos", []):
        if video.get("season") is None:
            continue
        rich_by_episode[(video.get("season"), video.get("episode"))] = video

    videos = []
    for cinemeta_video in cinemeta_data.get("videos", []):
        season = cinemeta_video.get("season")
        number = cinemeta_video.get("number")
        if season is None or number is None:
            continue

        episode = dict(cinemeta_video)
        episode["episode"] = number

        try:
            rich = rich_by_episode.get((int(season), int(number)))
        except (TypeError, ValueError):
            rich = None

        if rich:
            for field in ("thumbnail", "overview", "name", "rating"):
                episode[field] = rich.get(field) or episode.get(field)

        videos.append(episode)

    merged["videos"] = videos

    if cinemeta_data.get("imdbRating"):
        merged["rating"] = cinemeta_data["imdbRating"]
    if not merged.get("genres"):
        merged["genres"] = cinemeta_data.get("genres", [])
    if not merged.get("country") or merged.get("country") == "Unknown":
        merged["country"] = cinemeta_data.get("country", "Unknown")

    return merged


def is_anime(country, genres):
    """Route a title to AniList when it is Japanese or explicitly tagged anime.

    A heuristic, not a classifier: it exists because AniList has season-level
    data that TVMaze does not, and Japanese shows are where the two disagree
    most. False positives are cheap — AniList simply returns nothing and the
    caller falls back to TVMaze.
    """
    if country and ("JAPAN" in str(country).upper() or "JP" in str(country).upper()):
        return True
    if genres and "anime" in " ".join(genres).lower():
        return True
    return False


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
        # Rich metadata first, cheapest useful source first.
        meta = await self.client.get_series_details_tvmaze(imdb_id)
        if not meta:
            meta = await self.client.get_series_details_tmdb(imdb_id)
        if not meta:
            meta = await self.client.search_tvmaze_by_name(title)

        cinemeta_data = await self.client.get_series_details_cinemeta(imdb_id)
        return merge_series_metadata(meta, cinemeta_data)

    async def fetch_season_ratings(self, imdb_id, season_num):
        return await self.client.get_omdb_season_ratings(imdb_id, season_num)

    async def fetch_all_season_details(
        self, imdb_id, show_title, genres=[], country="Unknown", season_keys=[]
    ):
        if is_anime(country, genres):
            results = {}
            for season_num in season_keys:
                anilist_data = await self.client.get_anilist_season_data(
                    show_title, season_num
                )
                if anilist_data:
                    results[season_num] = anilist_data
            if results:
                return results

        return await self.client.get_all_seasons_details_tvmaze(imdb_id)

    async def get_streams(self, type_, id_):
        return await self.client.get_all_streams(type_, id_)

    async def search_imdb(self, query):
        return await self.client.search_imdb(query)

    async def close(self):
        await self.images.close()
        await self.client.close()
