# api/anilist.py
from config import ANILIST_URL

class AniListMixin:
    async def get_anilist_season_data(self, title, season_num):
        query = """
        query ($search: String) {
          Media (search: $search, type: ANIME, sort: SEARCH_MATCH) {
            description
            averageScore
            coverImage {
              extraLarge
            }
          }
        }
        """

        search_terms = []
        if season_num > 1:
            search_terms.append(f"{title} Season {season_num}")
            search_terms.append(f"{title} {season_num}")
        else:
            search_terms.append(f"{title}")
        
        for term in search_terms:
            try:
                resp = await self.client.post(
                    ANILIST_URL, 
                    json={'query': query, 'variables': {'search': term}}
                )
                
                if resp.status_code == 200:
                    data = resp.json().get('data', {}).get('Media')
                    if data:
                        desc = data.get('description', '')
                        if desc:
                            desc = desc.replace('<br>', '\n').replace('<i>', '').replace('</i>', '')
                        
                        score = data.get('averageScore')
                        if score: score = score / 10.0

                        return {
                            "poster": data.get('coverImage', {}).get('extraLarge'),
                            "overview": desc,
                            "rating": score 
                        }
            except:
                pass
        return None
