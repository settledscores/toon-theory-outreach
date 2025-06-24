import os
import time
import random
from duckduckgo_search import DDGS
from pyairtable import Api
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME)

search_queries = [
    'accounting firm site:.com',
    'bookkeeping agency site:.com',
    'tax preparation services site:.com',
    'business consulting services site:.com',
    'financial advisory site:.com'
]

print("🔎 Running DDG discovery scrape...")

for query in search_queries:
    print(f"🔍 Searching: \"{query}\"")
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
        for result in results:
            url = result.get("href") or result.get("url")
            if not url:
                continue
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            business_name = domain.replace("www.", "").split(".")[0].replace("-", " ").title()
            try:
                table.create({
                    "website url": url,
                    "business name": business_name
                })
                print(f"✅ Added: {business_name} ({url})")
            except Exception as e:
                print(f"❌ Failed to add {url}: {e}")
            time.sleep(random.uniform(1, 3))

print("🎉 Done.")
