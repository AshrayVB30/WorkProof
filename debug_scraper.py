import requests
from bs4 import BeautifulSoup
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperDebug")

def test_local_file():
    logger.info("Testing local reference_data.html...")
    try:
        with open("reference_data.html", "r", encoding="utf-8") as f:
            html = f.read()
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Test table extraction logic inline
        data = {}
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    if key and value:
                        data[key] = value
        
        logger.info(f"Local file extraction result: Found {len(data)} fields.")
        for k, v in list(data.items())[:5]:
            logger.info(f"  {k}: {v}")
            
    except Exception as e:
        logger.error(f"Local file test failed: {e}")

def test_url(url):
    logger.info(f"Testing URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Headers: {response.headers}")
        logger.info(f"Encoding (requests detected): {response.encoding}")
        logger.info(f"Apparent Encoding: {response.apparent_encoding}")
        
        # Check first few bytes
        logger.info(f"Content prefix (bytes): {response.content[:100]}")
        
        # Try decoding
        text = response.text
        logger.info(f"Content length (chars): {len(text)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        logger.info(f"BS4 Title: {soup.title}")
        
    except Exception as e:
        logger.error(f"URL test failed: {e}")

if __name__ == "__main__":
    test_local_file()
    print("-" * 50)
    # The URL from the user log
    BAD_URL = "http://109.199.108.38:2069/?q=QUNUQVNUeHg4MGltZzAwMDcuanBlZzs1NjY7MU4wZ01rSEg"
    test_url(BAD_URL)
