# api/base.py
import httpx
from config import HEADERS

class BaseClient:
    """
    Handles the raw HTTP connection. 
    Other API modules will inherit from this or use it.
    """
    def __init__(self):
        self.client = httpx.AsyncClient(headers=HEADERS, timeout=15.0)

    async def close(self):
        await self.client.aclose()
