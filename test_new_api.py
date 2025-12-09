# test_new_api.py
import asyncio
# Import the fully assembled client
from api import StremioClient 

async def main():
    print("--- 🧪 Testing FULL API Structure ---")
    client = StremioClient()
    
    # 1. Test TVMaze (Stranger Things)
    print("\n1. Testing TVMaze (Stranger Things)...")
    data = await client.get_series_details_tvmaze("tt4574334")
    if data:
        print(f"✅ SUCCESS: {data['name']} | Country: {data.get('country')}")
    else:
        print("❌ FAILED: TVMaze returned None.")

    # 2. Test AniList (Spy x Family)
    print("\n2. Testing AniList (Spy x Family Season 1)...")
    anime = await client.get_anilist_season_data("Spy x Family", 1)
    if anime:
        print(f"✅ SUCCESS: Found Poster & Rating ({anime.get('rating')})")
    else:
        print("❌ FAILED: AniList returned None.")

    # 3. Test OMDb (Ratings)
    print("\n3. Testing OMDb (Season 1 Ratings)...")
    ratings = await client.get_omdb_season_ratings("tt4574334", 1)
    if ratings:
        print(f"✅ SUCCESS: Retrieved {len(ratings)} episode ratings.")
    else:
        print("⚠️ OMDb skipped (Check API Key).")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
