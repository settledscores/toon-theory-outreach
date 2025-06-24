import time
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
from datetime import datetime
import os

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
api = Api(AIRTABLE_API_KEY)
table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

# ScraperAPI setup
SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")
BASE_URL = "https://themanifest.com/business-consulting/firms"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

MAX_PAGES = 2
MAX_COMPANIES_PER_PAGE = 5
ALLOWED_EMPLOYEE_RANGES = ["2 - 9", "10 - 49"]

def fetch_with_scraperapi(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        res = requests.get(proxy_url, headers=HEADERS)
        if res.status_code == 200:
            return res.text
        else:
            print(f"❌ Failed to fetch: {url} (status {res.status_code})")
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None

def extract_company_data(soup):
    records = []
    listings = soup.select(".views-row")
    for item in listings[:MAX_COMPANIES_PER_PAGE]:
        name_tag = item.select_one("h3 a")
        if not name_tag:
            continue

        profile_link = "https://themanifest.com" + name_tag.get("href")
        website_tag = item.select_one(".field--name-field-company-url a")
        website = website_tag.get("href") if website_tag else None

        location_tag = item.select_one(".field--name-field-location")
        location = location_tag.get_text(strip=True) if location_tag else None

        employee_tag = item.select_one(".field--name-field-employee-size")
        employee_range = employee_tag.get_text(strip=True) if employee_tag else None
        if employee_range not in ALLOWED_EMPLOYEE_RANGES:
            continue

        founded_tag = item.select_one(".field--name-field-founded")
        founded = founded_tag.get_text(strip=True) if founded_tag else None

        services_tag = item.select_one(".field--name-field-service-lines")
        services = services_tag.get_text(strip=True) if services_tag else None

        record = {
            "Website": website,
            "Clutch Profile": profile_link,
            "Location": location,
            "Employee Range": employee_range,
            "founded": founded,
            "service breakdown": services,
            "Date Added": datetime.utcnow().strftime("%Y-%m-%d")
        }
        records.append(record)
    return records

def upload_to_airtable(records):
    for record in records:
        try:
            table.create(record)
            print(f"✅ Uploaded: {record['Clutch Profile']}")
        except Exception as e:
            print(f"❌ Upload failed: {e}")

def main():
    print("🔄 Starting Manifest scraper (via ScraperAPI)...")
    for page in range(MAX_PAGES):
        url = f"{BASE_URL}?page={page}"
        print(f"🌐 Scraping: {url}")
        html = fetch_with_scraperapi(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        companies = extract_company_data(soup)
        if companies:
            upload_to_airtable(companies)
        time.sleep(60)  # 1 request per minute

    print("🎉 Done.")

if __name__ == "__main__":
    main()
