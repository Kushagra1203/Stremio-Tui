# core/cache.py
import httpx
from io import BytesIO
from PIL import Image

class ImageCache:
    def __init__(self):
        self._cache = {}

    async def get_image(self, url):
        """Downloads image if not cached, returns PIL Image object."""
        if not url: return None
        if url in self._cache:
            return self._cache[url]
            
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=4.0)
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content))
                    self._cache[url] = img
                    return img
        except:
            pass
        return None
