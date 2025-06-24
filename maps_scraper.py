import os
import requests
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

GOOGLE_MAPS_URL = "https://api.scraperapi.com/structured/google/maps/search"

QUERIES = [
    "accounting San Francisco",
    "bookkeeping New York",
    "tax consulting Chicago",
    "financial advisor Austin",
    "payroll services Seattle"
]

def search_maps(query):
    print(f"🔍 Searching: {query}")
    params = {
        "api_key": API_KEY,
        "query": query
    }
    try:
        response = requests.get(GOOGLE_MAPS_URL, params=params)
        response.raise_for_status()
        return response.json().get("organic_results", [])
    except Exception as e:
        print(f"❌ Failed: {e}")
        return []

def extract_businesses(results):
    for biz in results:
        name = biz.get("title")
        website = biz.get("website")
        if name and website:
            yield {"business name": name, "website url": website}

def main():
    api = Api(AIRTABLE_API_KEY)
    table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

    total_added = 0
    for query in QUERIES:
        results = search_maps(query)
        for business in extract_businesses(results):
            try:
                table.create(business)
                print(f"✅ Added: {business['business name']} - {business['website url']}")
                total_added += 1
                if total_added >= 10:
                    break
            except Exception as e:
                print(f"❌ Airtable Error: {e}")
        if total_added >= 10:
            break

    print("🎉 Done.")

if __name__ == "__main__":
    main()
