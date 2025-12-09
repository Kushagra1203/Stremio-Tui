# api/search.py

class SearchMixin:
    async def search_imdb(self, query: str):
        # We use a public suggestion API from IMDB (unofficial but stable)
        url = f"https://v3.sg.media-imdb.com/suggestion/x/{query}.json"
        try:
            resp = await self.client.get(url)
            data = resp.json()
            results = []
            for item in data.get('d', []):
                # Filter for Movies ('feature') and TV Series ('TV series')
                if item.get('q') in ['feature', 'TV series']:
                    results.append({
                        "title": item.get('l'),
                        "year": item.get('y'),
                        "type": item.get('q'),
                        "id": item.get('id'),
                        "poster": item.get('i', {}).get('imageUrl')
                    })
            return results
        except Exception:
            return []
