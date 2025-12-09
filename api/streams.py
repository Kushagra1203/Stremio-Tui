# api/streams.py
import urllib.parse
import asyncio
from config import PROVIDERS

class StreamsMixin:
    async def fetch_provider_stream(self, provider, type_, id_):
        streams = []
        status_code = None
        error_message = None
        
        try:
            parsed_url = urllib.parse.urlparse(provider['url'])
            base_url_path = parsed_url.path.replace("/manifest.json", "")
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{base_url_path}"
            
            url = f"{base_url}/stream/{type_}/{id_}.json"
            
            resp = await self.client.get(url)
            status_code = resp.status_code
            
            if resp.status_code == 200:
                data = resp.json()
                streams = data.get('streams', [])
            else:
                error_message = f"HTTP Error {status_code}"
                
        except Exception as e:
            error_message = f"Network Error: {type(e).__name__}"
        
        return {
            "name": provider['name'],
            "streams": streams,
            "status": status_code,
            "error": error_message,
        }

    async def get_all_streams(self, type_: str, id_: str):
        tasks = [self.fetch_provider_stream(p, type_, id_) for p in PROVIDERS]
        results_list = await asyncio.gather(*tasks)
        
        all_streams = []
        for result in results_list:
            if result and result.get('streams'):
                all_streams.extend(result['streams'])

        return all_streams
