import asyncio
from api import StremioClient

async def main():
    client = StremioClient()
    print("Fetching Trending Series...")
    
    # Call the function exactly how the Manager does
    results = await client.get_catalog_cinemeta("series", "top")
    
    if results:
        print(f"✅ Success! Found {len(results)} items.")
        print(f"   First Item: {results[0]['title']} ({results[0]['id']})")
    else:
        print("❌ Failed. Check 'debug_error.log' if it exists.")

    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
