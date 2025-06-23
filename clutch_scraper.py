import requests
from bs4 import BeautifulSoup
import time
import os
from pyairtable import Api
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
airtable = api.base(AIRTABLE_BASE_ID).table(TABLE_NAME)

ACCEPTED_LOCATIONS = [
    "United States", "USA", "UK", "United Kingdom", "Canada", "Australia",
    "Switzerland", "Germany", "Denmark", "Netherlands", "Poland"
]

ACCEPTED_EMPLOYEE_SIZES = ["2 - 9", "10 - 49"]

START_URL = "https://clutch.co/hr"

def is_valid_location(location_text):
    location_text = location_text.lower()
    return any(country.lower() in location_text for country in ACCEPTED_LOCATIONS)

def get_clutch_profiles(base_url, max_pages=20):
    companies = []
    for page in range(max_pages):
        url = f"{base_url}?page={page}"
        print(f"🌐 Scraping: {url}")
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if res.status_code != 200:
                print(f"❌ Invalid URL: {url} (status {res.status_code})")
                continue
        except Exception as e:
            print(f"❌ Request failed: {e}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        listings = soup.select(".provider-info")
        if not listings:
            print(f"⚠️ No listings found on page {page}")
            break

        for listing in listings:
            try:
                name_el = listing.select_one("h3 a")
                name = name_el.text.strip()
                clutch_profile = "https://clutch.co" + name_el["href"]

                location = listing.select_one(".location").text.strip()
                if not is_valid_location(location):
                    continue

                employees = listing.find(text="Employees")
                if employees:
                    employee_range = employees.find_next().text.strip()
                    if employee_range not in ACCEPTED_EMPLOYEE_SIZES:
                        continue
                else:
                    continue

                website_tag = listing.select_one("a.website-link__item")
                website = website_tag["href"].strip() if website_tag else ""

                services_block = listing.select(".field--name-field-service-lines .field__item")
                service_breakdown = ", ".join(s.text.strip() for s in services_block if s.text.strip()) if services_block else ""

                companies.append({
                    "business name": name,
                    "clutch profile": clutch_profile,
                    "location": location,
                    "employee range": employee_range,
                    "website": website,
                    "service breakdown": service_breakdown,
                    "date added": datetime.utcnow().strftime("%Y-%m-%d"),
                    "notes": "",
                })
            except Exception as e:
                print(f"⚠️ Error parsing company: {e}")
                continue

        time.sleep(1)
    return companies

def save_to_airtable(companies):
    print(f"💾 Saving {len(companies)} companies to Airtable...")
    for company in companies:
        try:
            airtable.create({
                "Website": company["website"],
                "Clutch Profile": company["clutch profile"],
                "Location": company["location"],
                "Employee Range": company["employee range"],
                "service breakdown": company["service breakdown"],
                "Date Added": company["date added"],
                "Notes": company["notes"]
            })
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ Airtable insert error: {e}")
            continue
    print("✅ Airtable upload complete.")

if __name__ == "__main__":
    print("🔄 Fetching existing records from Airtable...")
    records = airtable.all()
    print(f"📦 Existing records: {len(records)}")
    companies = get_clutch_profiles(START_URL, max_pages=30)
    print(f"📈 Total companies scraped: {len(companies)}")
    save_to_airtable(companies)
    print("🎉 Done.")
