import os
import requests
from urllib.parse import quote
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

HEADERS = {"X-API-KEY": SCRAPER_API_KEY}
SEARCH_QUERIES = [
    "accounting San Francisco",
    "bookkeeping New York"
]

def fetch_places(query):
    url = f"https://api.scraperapi.com/structured/maps/search?query={quote(query)}&limit=10"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("places", [])

def extract_business_data(place):
    return {
        "fields": {
            "website url": place.get("website"),
            "business name": place.get("title")
        }
    }

def main():
    print("📍 Running Google Maps business scraper (10 test results)...")
    for query in SEARCH_QUERIES:
        print(f"🔍 Querying: {query}")
        try:
            results = fetch_places(query)
            for place in results:
                if not place.get("website"):
                    continue
                data = extract_business_data(place)
                try:
                    table.create(data)
                    print(f"✅ Added: {data['fields']['business name']}")
                except Exception as airtable_error:
                    print(f"❌ Airtable error for {data['fields']}: {airtable_error}")
        except Exception as scrape_error:
            print(f"❌ Failed to fetch results for query '{query}': {scrape_error}")
    print("🎉 Scrape complete.")

if __name__ == "__main__":
    main()
