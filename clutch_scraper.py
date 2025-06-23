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
    "Referer": "https://google.com",
    "DNT": "1",
}

EXISTING_NAMES = set()

def fetch_existing_names():
    print("🔄 Fetching existing records from Airtable...")
    for record in airtable.all():
        name = record.get("fields", {}).get("business name", "")
        if name:
            EXISTING_NAMES.add(name.lower())

def get_clutch_profiles(url):
    print(f"🌐 Scraping: {url}")
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            print(f"❌ Invalid URL: {url} (status {res.status_code})")
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        companies = []

        for company in soup.select(".provider-info"):
            try:
                name = company.select_one("h3 a").text.strip()
                if name.lower() in EXISTING_NAMES:
                    continue

                profile_url = "https://clutch.co" + company.select_one("h3 a")["href"]
                location = company.select_one(".location").text.strip()
                employees = company.find(text="Employees").find_next().text.strip()

                # Check for accepted employee size
                if not any(s in employees for s in ["2-9", "10-49"]):
                    continue

                companies.append({
                    "name": name,
                    "clutch_profile": profile_url,
                    "location": location,
                    "employee range": employees,
                })
            except:
                continue

        print(f"✅ Found {len(companies)} companies from {url}")
        return companies

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {e}")
        return []

def save_to_airtable(companies):
    for company in companies:
        airtable.create({
            "business name": company["name"],
            "clutch profile": company["clutch_profile"],
            "location": company["location"],
            "employee range": company["employee range"],
        })
        print(f"📌 Saved: {company['name']}")
        time.sleep(0.3)

if __name__ == "__main__":
    fetch_existing_names()

    urls = [
        "https://clutch.co/us/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/hr/uk?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/au/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/se/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/ca/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/de/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/dk/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/ch/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/nl/hr?agency_size=10+-+49&agency_size=2+-+9",
        "https://clutch.co/pl/hr?agency_size=10+-+49&agency_size=2+-+9",
    ]

    for url in urls:
        companies = get_clutch_profiles(url)
        save_to_airtable(companies)

    print("🎉 Done scraping.")
