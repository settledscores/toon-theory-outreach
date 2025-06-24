import time
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
import os

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

# ScraperAPI setup
SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")
BASE_URL = "https://themanifest.com/business-consulting/firms"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

MAX_PAGES = 2  # Test mode: pages 0 and 1

def fetch_with_scraperapi(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        response = requests.get(proxy_url, headers=HEADERS)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ Failed to fetch: {url} (status {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Exception for {url}: {e}")
        return None

def upload_html_to_airtable(page_number, raw_html):
    try:
        record = {
            "Notes": f"HTML from page {page_number}",
            "Raw HTML": raw_html[:10000]  # limit to 10k chars
        }
        table.create(record)
        print(f"✅ Uploaded HTML from page {page_number}")
    except Exception as e:
        print(f"❌ Failed to upload HTML: {e}")

def main():
    print("🔄 Starting Manifest scraper (via ScraperAPI)...")
    for page in range(MAX_PAGES):
        url = f"{BASE_URL}?page={page}"
        print(f"🌐 Scraping: {url}")
        html = fetch_with_scraperapi(url)
        if html:
            upload_html_to_airtable(page, html)
        time.sleep(60)  # Respect rate limit

    print("🎉 Done.")

if __name__ == "__main__":
    main()
