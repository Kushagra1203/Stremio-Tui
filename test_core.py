# test_core.py
import asyncio
from core import MediaManager

async def main():
    print("--- 🧠 Testing Core Logic (The Brain) ---")
    manager = MediaManager()
    
    # 1. Stranger Things (Should fallback to TMDB since TVMaze ID lookup might fail)
    print("\n1. Fetching Stranger Things...")
    meta = await manager.get_unified_metadata("tt4574334", "Stranger Things")
    
    if meta:
        print(f"✅ SUCCESS: Found '{meta['name']}'")
        print(f"   Source: {meta.get('source')} (Did it fallback?)")
        print(f"   Country: {meta.get('country')}")
    else:
        print("❌ FAILED: Manager could not find data.")

    # 2. Spy x Family (Should Detect Anime via Country/Genre)
    print("\n2. Testing Anime Detection (Spy x Family)...")
    # We simulate passing the data that the UI would pass
    # (Mocking 'Japan' as country to trigger the logic)
    seasons = await manager.fetch_all_season_details(
        "tt13706018", 
        "Spy x Family", 
        genres=["Animation", "Action"], 
        country="Japan", 
        season_keys=[1]
    )
    
    if seasons and seasons.get(1):
        print(f"✅ SUCCESS: Got Season 1 Data")
        print(f"   Poster: {seasons[1].get('poster')[:30]}...")
    else:
        print("❌ FAILED: Anime detection failed.")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
