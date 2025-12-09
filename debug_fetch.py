# debug_fetch.py
import asyncio
import sys
import os
import subprocess
from core import StremioClient 

async def main_debug(stream_id):
    """Fetches and prints debug stream data synchronously."""
    print("\n" + "=" * 50)
    print(f"DEBUGGING STREAM ID: {stream_id}")
    print("CHECKING PROVIDERS...")
    print("=" * 50)
    
    # Initialize client and perform fetch
    try:
        client = StremioClient()
        # This will trigger the DEBUG prints inside core.py's fetch_provider_stream
        streams = await client.get_all_streams("series", stream_id)
        
        print("\n" + "=" * 50)
        if not streams:
            print(f"RESULT: ❌ Found 0 total streams.")
        else:
            print(f"RESULT: ✅ Success! Found {len(streams)} total streams.")
        print("=" * 50)
        
        await client.close()
        
    except Exception as e:
        print(f"\nFATAL DEBUG ERROR: {type(e).__name__} during client initialization/run.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_fetch.py <stremio_id_tt:s:e>")
        sys.exit(1)
    
    stremio_id = sys.argv[1]
    # asyncio.run is the synchronous entry point
    asyncio.run(main_debug(stremio_id))
