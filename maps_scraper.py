import os
import time
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

# Airtable setup
api = Api(API_KEY)
table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

QUERIES = [
    "accounting San Francisco",
    "bookkeeping New York",
    "tax consulting Chicago",
    "financial advisor Austin",
    "payroll services Seattle"
]

def search_maps(query):
    print(f"🔍 Searching: {query}")
    url = "http://api.scraperapi.com"
    params = {
        "api_key": API_KEY,
        "url": f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def parse_results(html):
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    results = []

    for a in links:
        href = a["href"]
        if "google.com/maps/place" in href:
            name = a.get_text(strip=True)
            if name and name not in [r["name"] for r in results]:
                results.append({
                    "name": name,
                    "url": href
                })
        if len(results) >= 10:
            break
    return results

def add_to_airtable(results):
    for result in results:
        try:
            table.create({
                "website url": result["url"],
                "business name": result["name"]
            })
        except Exception as e:
            print(f"❌ Failed to add {result['url']}: {e}")

def run():
    print("🔎 Running Google Maps scrape...")
    for query in QUERIES:
        html = search_maps(query)
        if not html:
            continue
        results = parse_results(html)
        add_to_airtable(results)
        time.sleep(3)  # be polite to API
    print("🎉 Done.")

if __name__ == "__main__":
    run()
