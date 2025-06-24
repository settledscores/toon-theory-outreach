# File: ddg_scraper.py
import os
import time
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME)

DDG_SEARCH_URL = "https://html.duckduckgo.com/html/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def search_duckduckgo(query):
    data = {"q": query}
    response = requests.post(DDG_SEARCH_URL, data=data, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if href and "http" in href:
            links.append(href)
        if len(links) == 5:
            break
    return links

def enrich_and_push(urls):
    for url in urls:
        record = {
            "website url": url,
            "platform": "DuckDuckGo",
            "Location": None,
            "Employee Range": None,
            "Revenue Tier": None,
            "Decision Maker Name": None,
            "Decision Maker Title": None,
            "Decision Maker Email": None,
            "Email Permutations": None,
            "Email Source": None,
            "LinkedIn URL": None,
            "Is Bootstrapped?": None,
            "Is Funded?": None,
            "Funding Flags": None,
            "Is Website Live?": None,
            "Notes": None,
            "Date Added": datetime.utcnow().isoformat(),
            "Status": "new",
            "founded": None,
            "service breakdown": None,
        }
        try:
            table.create(record)
            print(f"✅ Added: {url}")
        except Exception as e:
            print(f"❌ Failed to add {url}: {e}")

if __name__ == "__main__":
    print("🔎 Running DDG discovery scrape...")
    query = "accounting bookkeeping CFO services USA site:clutch.co OR site:goodfirms.co OR site:themanifest.com"
    urls = search_duckduckgo(query)
    enrich_and_push(urls)
    print("🎉 Done.")
