import requests
from bs4 import BeautifulSoup
import os
import time
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
airtable = api.base(AIRTABLE_BASE_ID).table(TABLE_NAME)

ACCEPTED_SIZES = ["2-9", "10-49"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URLS = [
    "https://clutch.co/us/hr",
    "https://clutch.co/hr/uk",
    "https://clutch.co/au/hr",
    "https://clutch.co/se/hr",
    "https://clutch.co/ca/hr",
    "https://clutch.co/de/hr",
    "https://clutch.co/dk/hr",
    "https://clutch.co/ch/hr",
    "https://clutch.co/nl/hr",
    "https://clutch.co/pl/hr",
    "https://clutch.co/consulting",
    "https://clutch.co/consulting/uk",
    "https://clutch.co/au/consulting",
    "https://clutch.co/us/accounting",
    "https://clutch.co/uk/accounting",
    "https://clutch.co/au/accounting",
    "https://clutch.co/law/tax",
    "https://clutch.co/us/law/corporate",
    "https://clutch.co/us/accounting/tax-services/tax-consulting",
    "https://clutch.co/us/law",
    "https://clutch.co/us/call-centers/sales-outsourcing",
    "https://clutch.co/us/hr/executive-search",
    "https://clutch.co/us/hr/staffing"
]

def scrape_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"❌ Invalid URL: {url} (status {response.status_code})")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        company_blocks = soup.select(".provider-info")
        results = []

        for block in company_blocks:
            try:
                name = block.select_one("h3 a").text.strip()
                profile_url = "https://clutch.co" + block.select_one("h3 a")["href"]
                location = block.select_one(".location").text.strip()
                employees = block.find(text="Employees").find_next().text.strip()

                if employees not in ACCEPTED_SIZES:
                    continue

                industry_tags = block.select(".field--name-field-service-lines .field__item")
                services_offered = [tag.text.strip() for tag in industry_tags]
                percentage_field = ", ".join(services_offered)

                results.append({
                    "business name": name,
                    "clutch profile": profile_url,
                    "location": location,
                    "employee range": employees,
                    "services breakdown": percentage_field
                })
            except Exception:
                continue
        return results
    except Exception as e:
        print(f"🔥 Error fetching {url}: {e}")
        return []

def get_existing_links():
    print("🔄 Fetching existing records from Airtable...")
    records = airtable.all()
    return set(record['fields'].get("clutch profile", "") for record in records)

def save_to_airtable(companies, existing_links):
    for company in companies:
        if company["clutch profile"] in existing_links:
            continue
        airtable.create(company)
        time.sleep(0.2)

def main():
    existing_links = get_existing_links()

    for base_url in BASE_URLS:
        for page in range(0, 20):
            paged_url = f"{base_url}?page={page}"
            print(f"🌐 Scraping: {paged_url}")
            companies = scrape_page(paged_url)
            if not companies:
                break
            save_to_airtable(companies, existing_links)

    print("🎉 Done scraping.")

if __name__ == "__main__":
    main()
