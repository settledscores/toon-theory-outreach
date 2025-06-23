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

ACCEPTED_LOCATIONS = [
    "United States", "United Kingdom", "Canada", "Australia",
    "Netherlands", "Germany", "Switzerland", "Denmark", "Poland", "Sweden"
]
ACCEPTED_EMPLOYEE_SIZES = ["2-9", "10-49"]
ACCEPTED_INDUSTRIES = [
    "Human Resources", "Consulting", "Sales", "Business Development", "Coaching",
    "Education", "Marketing", "Legal services", "Tax consulting", "Insurance",
    "Law", "HR/Staffing", "Management Consulting", "Sales Consulting"
]

MAX_PAGES = 50  # You can increase this if needed

def get_clutch_profiles():
    companies = []
    for page in range(0, MAX_PAGES):
        url = f"https://clutch.co/hr?page={page}"
        print(f"🌍 Scraping page {page + 1}: {url}")
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        providers = soup.select(".provider-info")

        for company in providers:
            try:
                name = company.select_one("h3 a").text.strip()
                profile_url = "https://clutch.co" + company.select_one("h3 a")["href"]
                location = company.select_one(".location").text.strip()
                employees = company.find(text="Employees").find_next().text.strip()
                industry_el = company.select_one(".field--name-field-service-lines .field__item")
                industry = industry_el.text.strip() if industry_el else ""

                # Count how many 'Undisclosed' values exist
                undisclosed_count = sum(
                    1 for field in company.select(".list-item span") if "undisclosed" in field.text.lower()
                )
                if undisclosed_count > 1:
                    print(f"⛔ Skipped (too many undisclosed): {name}")
                    continue

                if not any(loc in location for loc in ACCEPTED_LOCATIONS):
                    continue
                if not any(size in employees for size in ACCEPTED_EMPLOYEE_SIZES):
                    continue
                if not any(niche.lower() in industry.lower() for niche in ACCEPTED_INDUSTRIES):
                    continue

                print(f"✅ Matched: {name} | {location} | {employees} | {industry}")
                companies.append({
                    "name": name,
                    "clutch_profile": profile_url,
                    "location": location,
                    "employees": employees,
                    "industry": industry
                })

            except Exception as e:
                print(f"⚠️ Error parsing a company block: {e}")
                continue

        time.sleep(1)  # Be respectful to Clutch's servers

    print(f"🔎 Total matched companies across pages: {len(companies)}")
    return companies

def save_to_airtable(companies):
    for company in companies:
        print(f"📤 Saving to Airtable: {company['name']}")
        airtable.create({
            "business name": company["name"],
            "clutch profile": company["clutch_profile"],
            "location": company["location"],
            "employee range": company["employees"],
            "industry": company["industry"]
        })
        time.sleep(0.3)  # Avoid hitting Airtable rate limits

if __name__ == "__main__":
    companies = get_clutch_profiles()
    save_to_airtable(companies)
    print("✅ Script finished.")
