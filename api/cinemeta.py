# api/cinemeta.py
import logging

from config import CINEMETA_URL, CINEMETA_CATALOG_URL

log = logging.getLogger(__name__)


class CinemetaMixin:
    async def get_series_details_cinemeta(self, imdb_id: str, type_: str = "series"):
        url = f"{CINEMETA_URL}/{type_}/{imdb_id}.json"
        try:
            response = await self.client.get(url, follow_redirects=True)
        except Exception as exc:
            log.warning("cinemeta meta failed (%s) for %s",
                        type(exc).__name__, imdb_id)
            return {}

        if response.status_code != 200:
            log.warning("cinemeta meta returned HTTP %s for %s",
                        response.status_code, imdb_id)
            return {}

        return response.json().get("meta", {})

    async def get_catalog_cinemeta(self, type_: str, id_: str = "top"):
        """Fetch a catalogue.

        type_: 'movie' or 'series'.
        id_: 'top' (popular) or 'imdbRating' (top rated).
        """
        url = f"{CINEMETA_CATALOG_URL}/{type_}/{id_}.json"
        try:
            response = await self.client.get(url, follow_redirects=True)
        except Exception as exc:
            log.warning("cinemeta catalog failed (%s) for %s/%s",
                        type(exc).__name__, type_, id_)
            return []

        if response.status_code != 200:
            log.warning("cinemeta catalog returned HTTP %s for %s/%s",
                        response.status_code, type_, id_)
            return []

        results = []
        for meta in response.json().get("metas", []):
            # Cinemeta carries the IMDb id in its "id" field.
            imdb_id = meta.get("id")
            if not imdb_id:
                continue
            results.append({
                "title": meta.get("name"),
                "year": meta.get("releaseInfo", "")[:4],
                "type": meta.get("type"),
                "id": imdb_id,
                "poster": meta.get("poster"),
            })
        return results
