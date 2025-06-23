import requests
from bs4 import BeautifulSoup
import time
import os
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
airtable = api.base(AIRTABLE_BASE_ID).table(TABLE_NAME)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    "DNT": "1",
    "Connection": "keep-alive"
}

ACCEPTED_SIZES = ["2-9", "10-49"]
EXISTING_NAMES = set()

def fetch_existing_names():
    print("🔄 Fetching existing records from Airtable...")
    for record in airtable.all():
        name = record.get("fields", {}).get("business name", "")
        if name:
            EXISTING_NAMES.add(name.lower())

def get_clutch_profiles(base_url):
    all_companies = []
    for page in range(1, 50):  # Adjust upper bound as needed
        paginated_url = f"{base_url}&page={page}"
        print(f"🌐 Scraping: {paginated_url}")
        try:
            res = requests.get(paginated_url, headers=HEADERS, timeout=10)
            if res.status_code == 403:
                print(f"❌ Forbidden (403): {paginated_url}")
                break
            elif res.status_code != 200:
                print(f"❌ Failed: {paginated_url} (status {res.status_code})")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".provider-info")
            if not cards:
                print(f"⛔ No companies found on page {page}")
                break

            for company in cards:
                try:
                    name = company.select_one("h3 a").text.strip()
                    if name.lower() in EXISTING_NAMES:
                        continue

                    profile_url = "https://clutch.co" + company.select_one("h3 a")["href"]
                    location = company.select_one(".location").text.strip()
                    employees = company.find(text="Employ
