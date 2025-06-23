import requests
from bs4 import BeautifulSoup
import time
import os
import re
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
airtable = api.base(AIRTABLE_BASE_ID).table(TABLE_NAME)

CLUTCH_URLS = [
    "https://clutch.co/us/hr?",
    "https://clutch.co/hr/uk?",
    "https://clutch.co/au/hr?",
    "https://clutch.co/se/hr?",
    "https://clutch.co/ca/hr?",
    "https://clutch.co/de/hr?",
    "https://clutch.co/dk/hr?",
    "https://clutch.co/ch/hr?",
    "https://clutch.co/nl/hr?",
    "https://clutch.co/pl/hr?"
]

ACCEPTED_EMPLOYEE_SIZES = ["2-9", "10-49"]
ACCEPTED_INDUSTRIES = [
    "Human Resources", "Consulting", "Sales", "Business Development", "Coaching",
    "Education", "Marketing", "Legal services", "Tax consulting", "Insurance",
    "Law", "HR/Staffing", "Management Consulting", "Sales Consulting"
]

MAX_PAGES = 50

def bucket_year(year):
    try:
        year = int(year)
        if 2000 <= year < 2005: return "2000–2005"
        if 2005 <= year < 2010: return "2005–2010"
        if 2010 <= year < 2015: return "2010–2015"
        if 2015 <= year < 2020: return "2015–2020"
        if 2020 <= year <= 2025: return "2020–2025"
    except:
        return None

def extract_founded_year(profile_url):
    try:
        res = requests.get(profile_url)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text().lower()
        match = re.search(r'founded\s*(in)?\s*(\d{4})', text)
        if match:
            return bucket_year(match.group(2))
    except:
        return None
    return None

def get_clutch_profiles():
    companies = []

    for base_url in CLUTCH_URLS:
        for page in range(0, MAX_PAGES):
            url = f"{base_url}page={page}"
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

                    # Count how many 'Undisclosed' fields are in the block
                    undisclosed_count = sum(
                        1 for field in company.select(".list-item span") if "undisclosed" in field.text.lower()
                    )
                    if undisclosed_count > 1:
                        print(f"⛔ Skipped (undisclosed): {name}")
                        continue

                    if not any(size in employees for size in ACCEPTED_EMPLOYEE_SIZES):
                        continue
                    if not any(niche.lower() in industry.lower() for niche in ACCEPTED_INDUSTRIES):
                        continue

                    founding_bucket = extract_founded_year(profile_url)
                    if not founding_bucket:
                        print(f"⛔ Skipped (no founding year): {name}")
                        continue

                    print(f"✅ Matched: {name} ({founding_bucket})")
                    companies.append({
                        "name": name,
                        "clutch_profile": profile_url,
                        "location": location,
                        "employees": employees,
                        "industry": industry,
                        "founded": founding_bucket
                    })

                except Exception as e:
                    print(f"⚠️ Error parsing a company block: {e}")
                    continue

            time.sleep(1)

    print(f"\n🔎 Total matched companies: {len(companies)}")
    return companies

def save_to_airtable(companies):
    for company in companies:
        print(f"📤 Saving to Airtable: {company['name']}")
        airtable.create({
            "business name": company["name"],
            "clutch profile": company["clutch_profile"],
            "location": company["location"],
            "employee range": company["employees"],
            "industry": company["industry"],
            "founded": company["founded"]
        })
        time.sleep(0.3)

if __name__ == "__main__":
    companies = get_clutch_profiles()
    save_to_airtable(companies)
    print("✅ Script finished.")
