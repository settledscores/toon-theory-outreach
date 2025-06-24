import os
import re
import time
import random
import requests
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pyairtable import Api

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
AIRTABLE = Api(AIRTABLE_API_KEY).base(AIRTABLE_BASE_ID)

# Custom DDG search queries to inject
SEARCH_QUERIES = [
    '"accounting firm" "contact us" site:.com',
    '"bookkeeping agency" site:.com',
    '"tax preparation services" "home page" site:.com',
    '"business consulting services" "request a quote" site:.com',
    '"financial advisory" site:.com'
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36"
}

DDG_SEARCH_URL = "https://html.duckduckgo.com/html/?q={query}"


def clean_url(raw_url):
    if not raw_url:
        return None
    # Extract final destination from DDG redirect
    match = re.search(r"uddg=(.*?)(&|$)", raw_url)
    if match:
        return requests.utils.unquote(match.group(1))
    return raw_url


def extract_domain_name(url):
    domain = urlparse(url).netloc
    return domain.replace("www.", "") if domain else None


def infer_business_name_from_title(title):
    if not title:
        return None
    parts = title.split("|")
    return parts[0].strip() if parts else title.strip()


def search_and_parse_ddg(query):
    url = DDG_SEARCH_URL.format(query=requests.utils.quote(query))
    print(f"🔍 Searching: {query}")
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    for a in soup.select("a.result__a"):
        final_url = clean_url(a.get("href"))
        title = a.get_text()
        if not final_url or any(x in final_url for x in ["clutch.co", "themanifest.com", "goodfirms.co"]):
            continue

        domain = extract_domain_name(final_url)
        business_name = infer_business_name_from_title(title)

        results.append({
            "Website URL": final_url,
            "Business Name": business_name,
            "Platform": "ddg"
        })
        if len(results) >= 5:
            break

    return results


def push_to_airtable(records):
    for record in records:
        try:
            AIRTABLE.table(SCRAPER_TABLE_NAME).create({
                "website url": record["Website URL"],
                "platform": record["Platform"],
                "business name": record["Business Name"],
                "Date Added": datetime.now().strftime("%Y-%m-%d")
            })
            print(f"✅ Added {record['Website URL']}")
        except Exception as e:
            print(f"❌ Failed to add {record['Website URL']}: {e}")


if __name__ == "__main__":
    print("🔎 Running DDG discovery scrape...")
    total_records = []
    for query in SEARCH_QUERIES:
        records = search_and_parse_ddg(query)
        total_records.extend(records)
        time.sleep(random.uniform(2, 4))

    push_to_airtable(total_records)
    print("🎉 Done.")
