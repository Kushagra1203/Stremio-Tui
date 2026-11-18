# core/cache.py
import logging
from collections import OrderedDict
from io import BytesIO

import httpx
from PIL import Image

log = logging.getLogger(__name__)

DEFAULT_MAX_ENTRIES = 64
DEFAULT_TIMEOUT = 4.0


class ImageCache:
    """Bounded in-memory cache for poster images.

    Posters are the largest objects the UI holds, so the cache is not allowed to
    grow without limit: once ``max_entries`` is reached the least-recently-used
    entry is evicted. The HTTP client is reused across requests so connections
    are pooled instead of reopened for every poster.

    The cache is deliberately in memory only. Posters are best-effort decoration;
    a cold start just re-downloads them, so a disk tier would add an invalidation
    problem for no real gain at this size.
    """

    def __init__(self, max_entries=DEFAULT_MAX_ENTRIES, client=None,
                 timeout=DEFAULT_TIMEOUT):
        self.max_entries = max_entries
        self.timeout = timeout
        self._client = client
        self._owns_client = client is None
        self._entries = OrderedDict()

    def _get_client(self):
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def get_image(self, url):
        """Return a PIL image for ``url``, downloading it at most once."""
        if not url:
            return None

        cached = self._entries.get(url)
        if cached is not None:
            self._entries.move_to_end(url)
            return cached

        try:
            response = await self._get_client().get(url)
        except httpx.HTTPError as exc:
            log.warning("poster download failed (%s): %s", type(exc).__name__, url)
            return None

        if response.status_code != 200:
            log.warning("poster download returned HTTP %s: %s",
                        response.status_code, url)
            return None

        try:
            image = Image.open(BytesIO(response.content))
        except Exception:
            log.warning("poster could not be decoded: %s", url)
            return None

        self._store(url, image)
        return image

    def _store(self, url, image):
        self._entries[url] = image
        self._entries.move_to_end(url)
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    async def close(self):
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None
