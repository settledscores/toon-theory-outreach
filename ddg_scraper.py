import requests
from bs4 import BeautifulSoup
from pyairtable import Table
from datetime import datetime
import os

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

DDG_QUERY = "site:clutch.co OR site:manifest.com OR site:goodfirms.co accounting company"
DDG_URL = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(DDG_QUERY)}"

def get_duckduckgo_results():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(DDG_URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.select("a.result__a")
    urls = []

    for link in links:
        url = link.get("href")
        name = link.text.strip()
        if url and name:
            urls.append((url, name))
        if len(urls) >= 5:
            break

    return urls

def push_to_airtable(urls):
    table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME)
    for url, name in urls:
        try:
            table.create({
                "website url": url,
                "business name": name
            })
            print(f"✅ Added {url}")
        except Exception as e:
            print(f"❌ Failed to add {url}: {e}")

if __name__ == "__main__":
    print("🔎 Running DDG discovery scrape...")
    results = get_duckduckgo_results()
    push_to_airtable(results)
    print("🎉 Done.")
