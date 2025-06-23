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

ACCEPTED_EMPLOYEE_SIZES = ["2-9", "10-49"]

SCRAPE_URLS = [
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
    # Tax Law
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=840",
    "https://clutch.co/law/tax?agency_size=2+-+9&agency_size=10+-+49&geona_id=124",
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=826",
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=53792",
    "https://clutch.co/law/tax?agency_size=10+-+49&agency_size=2+-+9&geona_id=276",
    "https://clutch.co/law/tax?agency_size=2+-+9&agency_size=10+-+49&geona_id=756",
    # Corporate Law
    "https://clutch.co/us/law/corporate?agency_size=10+-+49&agency_size=2+-+9",
    # Tax Consulting
    "https://clutch.co/us/accounting/tax-services/tax-consulting?agency_size=10+-+49&agency_size=2+-+9",
    # Law Firms
    "https://clutch.co/us/law?agency_size=2+-+9&agency_size=10+-+49",
    # Sales Outsourcing
    "https://clutch.co/us/call-centers/sales-outsourcing?agency_size=10+-+49&agency_size=2+-+9",
    # Executive Search
    "https://clutch.co/us/hr/executive-search?agency_size=2+-+9&agency_size=10+-+49",
    # Staffing
    "https://clutch.co/us/hr/staffing?agency_size=10+-+49&agency_size=2+-+9"
]

def get_existing_names():
    print("🔄 Fetching existing records from Airtable...")
    existing = set()
    for page in airtable.iterate():
        for record in page:
            name = record.get("fields", {}).get("business name", "")
            if name:
                existing.add(name.lower())
    return existing

def get_clutch_profiles(url):
    try:
        print(f"🌐 Scraping: {url}")
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"❌ Invalid URL: {url} (status {res.status_code})")
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        companies = []

        for company in soup.select(".provider-info"):
            try:
                name = company.select_one("h3 a").text.strip()
                profile_url = "https://clutch.co" + company.select_one("h3 a")["href"]
                employees = company.find(text="Employees").find_next().text.strip()
                if not any(size in employees for size in ACCEPTED_EMPLOYEE_SIZES):
                    continue
                location = company.select_one(".location").text.strip()
                industry_tag = company.select_one(".field--name-field-service-lines .field__item")
                industry = industry_tag.text.strip() if industry_tag else "unspecified"

                companies.append({
                    "name": name,
                    "clutch_profile": profile_url,
                    "location": location,
                    "employees": employees,
                    "industry": industry
                })
            except Exception:
                continue

        return companies

    except Exception as e:
        print(f"❌ Failed to scrape {url}: {str(e)}")
        return []

def save_to_airtable(companies, existing_names):
    for company in companies:
        name = company["name"].lower()
        if name in existing_names:
            continue
        airtable.create({
            "business name": company["name"],
            "clutch profile": company["clutch_profile"],
            "location": company["location"],
            "employee range": company["employees"],
            "industry": company["industry"],
            "service breakdown": ""  # Placeholder
        })
        print(f"✅ Added: {company['name']}")
        time.sleep(0.3)

if __name__ == "__main__":
    all_companies = []
    existing_names = get_existing_names()

    for url in SCRAPE_URLS:
        companies = get_clutch_profiles(url)
        save_to_airtable(companies, existing_names)
        time.sleep(2)

    print("🎉 Done scraping.")
