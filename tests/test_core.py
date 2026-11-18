import io
import unittest

from PIL import Image

from core.cache import ImageCache
from core.manager import is_anime, merge_series_metadata


def cinemeta_show(videos, **extra):
    show = {
        "name": "Test Show",
        "videos": videos,
        "genres": ["Drama"],
        "country": "United States",
    }
    show.update(extra)
    return show


def rich_show(videos, **extra):
    show = {"name": "Test Show", "videos": videos, "genres": ["Drama"]}
    show.update(extra)
    return show


class MergeSeriesMetadataTests(unittest.TestCase):
    def test_cinemeta_decides_which_episodes_exist(self):
        cinemeta = cinemeta_show([
            {"season": 1, "number": 1},
            {"season": 1, "number": 2},
        ])
        rich = rich_show([
            {"season": 1, "episode": 1},
            {"season": 1, "episode": 2},
            {"season": 9, "episode": 9},  # stray entry the catalogue does not have
        ])

        merged = merge_series_metadata(rich, cinemeta)

        self.assertEqual([v["episode"] for v in merged["videos"]], [1, 2])

    def test_rich_fields_fill_in_matching_episodes(self):
        cinemeta = cinemeta_show([{"season": 1, "number": 1, "name": None}])
        rich = rich_show([
            {"season": 1, "episode": 1, "name": "Pilot", "overview": "It begins.",
             "thumbnail": "http://img/1.jpg", "rating": 8.1},
        ])

        episode = merge_series_metadata(rich, cinemeta)["videos"][0]

        self.assertEqual(episode["name"], "Pilot")
        self.assertEqual(episode["overview"], "It begins.")
        self.assertEqual(episode["thumbnail"], "http://img/1.jpg")
        self.assertEqual(episode["rating"], 8.1)

    def test_unmatched_episode_keeps_cinemeta_values(self):
        cinemeta = cinemeta_show([{"season": 1, "number": 1, "name": "From Cinemeta"}])
        rich = rich_show([])

        episode = merge_series_metadata(rich, cinemeta)["videos"][0]

        self.assertEqual(episode["name"], "From Cinemeta")
        self.assertEqual(episode["episode"], 1)

    def test_episode_number_is_normalised_onto_episode(self):
        cinemeta = cinemeta_show([{"season": 2, "number": 7}])

        merged = merge_series_metadata(None, cinemeta)

        self.assertEqual(merged["videos"][0]["episode"], 7)
        self.assertEqual(merged["videos"][0]["number"], 7)

    def test_no_cinemeta_returns_rich_metadata_untouched(self):
        rich = rich_show([{"season": 1, "episode": 1}])

        self.assertIs(merge_series_metadata(rich, {}), rich)

    def test_no_rich_source_returns_cinemeta_show(self):
        cinemeta = cinemeta_show([{"season": 1, "number": 3}])

        merged = merge_series_metadata(None, cinemeta)

        self.assertEqual(merged["name"], "Test Show")
        self.assertEqual(len(merged["videos"]), 1)

    def test_videos_missing_season_or_number_are_skipped(self):
        cinemeta = cinemeta_show([
            {"season": 1, "number": 1},
            {"season": None, "number": 2},
            {"season": 1, "number": None},
        ])

        merged = merge_series_metadata(rich_show([]), cinemeta)

        self.assertEqual(len(merged["videos"]), 1)

    def test_cinemeta_rating_wins_and_fills_missing_fields(self):
        cinemeta = cinemeta_show([], imdbRating="9.0", country="Japan")
        rich = rich_show([], rating=7.5, genres=[], country="Unknown")

        merged = merge_series_metadata(rich, cinemeta)

        self.assertEqual(merged["rating"], "9.0")
        self.assertEqual(merged["genres"], ["Drama"])
        self.assertEqual(merged["country"], "Japan")

    def test_inputs_are_not_mutated(self):
        cinemeta = cinemeta_show([{"season": 1, "number": 1}])
        rich = rich_show([{"season": 1, "episode": 1}])
        cinemeta_before = cinemeta.copy()
        rich_before = rich.copy()

        merge_series_metadata(rich, cinemeta)

        self.assertEqual(cinemeta["videos"], cinemeta_before["videos"])
        self.assertEqual(rich["videos"], rich_before["videos"])


class IsAnimeTests(unittest.TestCase):
    def test_japanese_country_routes_to_anime(self):
        self.assertTrue(is_anime("Japan", []))
        self.assertTrue(is_anime("JP", ["Action"]))

    def test_anime_genre_routes_to_anime(self):
        self.assertTrue(is_anime("Unknown", ["Animation", "Anime"]))

    def test_ordinary_drama_is_not_anime(self):
        self.assertFalse(is_anime("United States", ["Drama", "Comedy"]))

    def test_missing_fields_are_not_anime(self):
        self.assertFalse(is_anime(None, None))


def png_bytes():
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(buffer, format="PNG")
    return buffer.getvalue()


class FakeResponse:
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


class FakeClient:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.calls = []

    async def get(self, url):
        self.calls.append(url)
        return FakeResponse(self.status_code, self.payload)


class ImageCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_repeat_request_is_served_from_cache(self):
        client = FakeClient(png_bytes())
        cache = ImageCache(client=client)

        await cache.get_image("http://img/1.png")
        await cache.get_image("http://img/1.png")

        self.assertEqual(len(client.calls), 1)

    async def test_least_recently_used_entry_is_evicted(self):
        cache = ImageCache(max_entries=2, client=FakeClient(png_bytes()))

        await cache.get_image("a")
        await cache.get_image("b")
        await cache.get_image("a")  # touch "a" so "b" becomes the oldest
        await cache.get_image("c")  # evicts "b"

        self.assertEqual(list(cache._entries), ["a", "c"])

    async def test_empty_url_is_not_requested(self):
        client = FakeClient(png_bytes())
        cache = ImageCache(client=client)

        self.assertIsNone(await cache.get_image(""))
        self.assertEqual(client.calls, [])

    async def test_failed_download_is_not_cached(self):
        cache = ImageCache(client=FakeClient(b"", status_code=404))

        self.assertIsNone(await cache.get_image("http://img/missing.png"))
        self.assertEqual(len(cache._entries), 0)


if __name__ == "__main__":
    unittest.main()
