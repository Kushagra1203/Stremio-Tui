import asyncio
import sys
import os
import time
from core import StremioClient # Needs StremioClient class
from controllers import SeriesController # Needs SeriesController class

async def check_torrent_fetch(imdb_id, title):
    """
    Executes the metadata and stream fetching for a specific show ID.
    Prints the results and any debug messages for all providers.
    """
    start_time = time.time()
    print("-" * 60)
    print(f"DIAGNOSTIC TEST: {title} ({imdb_id})")
    print("-" * 60)
    
    try:
        client = StremioClient()
        controller = SeriesController(client)
        
        # 1. Fetch metadata to get Season/Episode structure and confirm the show name/ID
        meta = await controller.get_unified_metadata(imdb_id, title)
        
        if not meta or not meta.get('videos'):
            print("❌ METADATA FAIL: Could not fetch unified metadata (TVMaze/TMDB fallback failed).")
            print("   (Ensure IMDB ID is correct and network is active.)")
            await client.close()
            return

        # 2. Use the first available episode's ID for testing streams
        # We assume Season 1, Episode 1 exists.
        ep = meta['videos'][0]
        stream_id = f"{imdb_id}:{ep['season']}:{ep['episode']}"
        
        print(f"✅ METADATA SUCCESS: Source={meta.get('source')} | Stream ID to test: {stream_id}")
        
        # 3. Fetch Streams (This triggers the network and debug prints in core.py)
        # We cannot just call get_all_streams here as it returns the final list.
        # We need to manually call fetch_provider_stream for targeted debugging.
        
        # Manually define the providers to print detailed results
        providers_to_check = [
            {"name": "Torrentio", "url": "https://torrentio.strem.fun/qualityfilter=480p,other,scr,cam,unknown/manifest.json"},
            {"name": "Comet", "url": "https://comet.elfhosted.com/manifest.json"}
        ]

        tasks = [client.fetch_provider_stream(p, "series", stream_id) for p in providers_to_check]
        results_list = await asyncio.gather(*tasks)

        # 4. Analyze Results
        total_streams = 0
        
        for result in results_list:
            provider_name = result['name']
            stream_count = len(result['streams'])
            total_streams += stream_count
            
            status_text = f"Status: {result['status']}" if result['status'] else ""
            error_text = f"Error: {result['error']}" if result['error'] else ""
            
            if stream_count > 0:
                print(f"🟢 {provider_name:<10}: FOUND {stream_count} streams. {status_text}")
            else:
                print(f"🔴 {provider_name:<10}: FAILED. {status_text} {error_text}")
                
        print("-" * 60)
        print(f"SUMMARY: Total Streams Found: {total_streams}")
        print(f"TIME TAKEN: {time.time() - start_time:.2f}s")
        print("-" * 60)
        
        await client.close()

    except Exception as e:
        print(f"FATAL SCRIPT ERROR: {type(e).__name__} - {e}")
        print("Ensure all modules are installed and core.py is up-to-date.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python check_torrentio.py <imdb_id> <title>")
        print("Example: python check_torrentio.py tt4574334 'Stranger Things'")
        sys.exit(1)
    
    imdb_id = sys.argv[1]
    title = sys.argv[2]
    
    # Run the async script
    asyncio.run(check_torrent_fetch(imdb_id, title))
