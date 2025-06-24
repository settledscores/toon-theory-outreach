import requests
from bs4 import BeautifulSoup
from pyairtable import Api
import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

URL = "https://curlie.org/Business/Accounting/Firms/Accountants/North_America/United_States/California/"

def scrape_curlie(url, limit=10):
    print(f"🔍 Scraping: {url}")
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for li in soup.select("div.site-title a")[:limit]:
        name = li.text.strip()
        link = li["href"]
        if link.startswith("/"):
            link = "https://curlie.org" + link
        results.append((name, link))

    return results

def push_to_airtable(data):
    for name, link in data:
        try:
            table.create({
                "business name": name,
                "website url": link
            })
            print(f"✅ Added: {name} – {link}")
        except Exception as e:
            print(f"❌ Failed to add {link}: {e}")

if __name__ == "__main__":
    entries = scrape_curlie(URL, limit=10)
    push_to_airtable(entries)
