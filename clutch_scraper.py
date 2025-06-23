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

ACCEPTED_SIZES = ["2-9", "10-49"]

ALL_URLS = [
    # HR
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
    # Consulting
    "https://clutch.co/consulting?agency_size=10+-+49&agency_size=2+-+9&geona_id=840",
    "https://clutch.co/consulting/uk?agency_size=10+-+49&agency_size=2+-+9",
    "https://clutch.co/au/consulting?agency_size=10+-+49&agency_size=2+-+9",
    # Accounting
    "https://clutch.co/us/accounting?agency_size=10+-+49&agency_size=2+-+9",
    "https://clutch.co/uk/accounting?agency_size=10+-+49&agency_size=2+-+9",
    "https://clutch.co/au/accounting?agency_size=10+-+49&agency_size=2+-+9",
    # Tax law
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=840",
    "https://clutch.co/law/tax?agency_size=2+-+9&agency_size=10+-+49&geona_id=124",
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=826",
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=53792",
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=276",
    "https://clutch.co/law/tax?agency_size=2+-+9&agency_size=10+-+49&geona_id=756",
    # Corporate law
    "https://clutch.co/us/law/corporate?agency_size=10+-+49&agency_size=2+-+9",
    # Tax consulting
    "https://clutch.co/us/accounting/tax-services/tax-consulting?agency_size=10+-+49&agency_size=2+-+9",
    # Law firms
    "https://clutch.co/us/law?agency_size=2+-+9&agency_size=10+-+49",
    # Sales outsourcing
    "https://clutch.co/us/call-centers/sales-outsourcing?agency_size=10+-+49&agency_size=2+-+9",
    # Executive search
    "https://clutch.co/us/hr/executive-search?agency_size=2+-+9&agency_size=10+-+49",
    # Staffing
    "https://clutch.co/us/hr/staffing?agency_size=10+-+49&agency_size=2+-+9"
]

def get_existing_names():
    print("🔄 Fetching existing records from Airtable...")
    names = set()
    for page in airtable.iterate():
        for record in page:
            name = record["fields"].get("business name", "").strip().lower()
            if name:
                names.add(name)
    return names

def scrape_company_cards(url, existing_names):
    companies = []
    for page_num in range(0, 20):  # max 20 pages
        paged_url = f"{url}&page={page_num}"
        print(f"🌐 Scraping: {paged_url}")
        try:
            res = requests.get(paged_url, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code != 200:
                print(f"❌ Invalid URL: {paged_url} (status {res.status_code})")
                break
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(".provider-info")
            if not cards:
                print(f"⛔ No cards found on page {page_num}")
                break

            for company in cards:
                try:
                    name = company.select_one("h3 a").text.strip()
                    if name.lower() in existing_names:
                        continue

                    profile_url = "https://clutch.co" + company.select_one("h3 a")["href"]
                    location = company.select_one(".location").text.strip()

                    employees_tag = company.find(text="Employees")
                    employees = employees_tag.find_next().text.strip() if employees_tag else "Unknown"

                    if not any(size in employees for size in ACCEPTED_SIZES):
                        continue

                    companies.append({
                        "business name": name,
                        "clutch profile": profile_url,
                        "location": location,
                        "employee range": employees
                    })

                    existing_names.add(name.lower())
                except Exception as e:
                    print(f"⚠️ Skipped a company due to error: {e}")
                    continue

        except Exception as e:
            print(f"💥 Failed to fetch {paged_url}: {e}")
            continue

        time.sleep(1)
    return companies

def save_to_airtable(companies):
    for company in companies:
        airtable.create(company)
        print(f"✅ Added: {company['business name']}")
        time.sleep(0.3)  # prevent rate limiting

if __name__ == "__main__":
    all_companies = []
    seen_names = get_existing_names()
    for url in ALL_URLS:
        scraped = scrape_company_cards(url, seen_names)
        print(f"📦 Found {len(scraped)} new companies from: {url}")
        all_companies.extend(scraped)

    print(f"💾 Saving {len(all_companies)} companies to Airtable...")
    save_to_airtable(all_companies)
    print("🎉 Done scraping.")
