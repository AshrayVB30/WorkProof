import asyncio
import json
from server import process_image_url

async def main():
    url = "http://109.199.108.38:2069/?q=QUNUQVNUeHg4MGltZzAwMTAuanBlZzs1Njk7NVJmb3g0Nzg"
    print(f"Testing OCR for URL: {url}")
    try:
        data = await process_image_url(url)
        print("\n--- EXTRACTED DATA ---\n")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
