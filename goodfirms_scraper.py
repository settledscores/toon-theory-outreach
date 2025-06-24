import os
import time
import requests
from bs4 import BeautifulSoup
from pyairtable import Api

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
api = Api(AIRTABLE_API_KEY)
table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

# Scraper settings
BASE_URL = "https://www.goodfirms.co/business-services/accounting/usa"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}
MAX_PAGES = 2
MAX_COMPANIES_PER_PAGE = 5

def fetch_page(url):
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ Failed to fetch: {url} (status {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def extract_company_data(html):
    soup = BeautifulSoup(html, "html.parser")
    listings = soup.select(".company_list li")[:MAX_COMPANIES_PER_PAGE]
    results = []

    for item in listings:
        name_tag = item.select_one("h3.company-name a")
        if not name_tag:
            continue

        profile_url = "https://www.goodfirms.co" + name_tag["href"]
        website_tag = item.select_one("a.website-link")
        website = website_tag["href"] if website_tag else None

        location_tag = item.select_one(".company-country span")
        location = location_tag.text.strip() if location_tag else None

        employees_tag = item.select_one(".employees span")
        employee_range = employees_tag.text.strip() if employees_tag else None

        services_tag = item.select_one(".service-focus span")
        service_breakdown = services_tag.text.strip() if services_tag else None

        record = {
            "Clutch Profile": profile_url,
            "Website": website,
            "Location": location,
            "Employee Range": employee_range,
            "service breakdown": service_breakdown,
        }
        results.append(record)

    return results

def upload_to_airtable(records):
    for record in records:
        try:
            table.create(record)
            print(f"✅ Uploaded: {record.get('Clutch Profile')}")
        except Exception as e:
            print(f"❌ Airtable upload error: {e}")

def main():
    print("🔄 Starting GoodFirms scraper...")
    for page in range(0, MAX_PAGES):
        page_url = f"{BASE_URL}?page={page}"
        print(f"🌐 Scraping: {page_url}")
        html = fetch_page(page_url)
        if not html:
            continue
        records = extract_company_data(html)
        if records:
            upload_to_airtable(records)
        time.sleep(60)
    print("🎉 Scraping complete.")

if __name__ == "__main__":
    main()
