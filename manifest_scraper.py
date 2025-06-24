import time
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

MAX_PAGES = 2
MAX_COMPANIES_PER_PAGE = 5

def fetch_with_scraperapi(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}&render=true"
    try:
        response = requests.get(proxy_url, headers=HEADERS)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ Failed to fetch: {url} (status {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Exception for {url}: {e}")
        return None

def extract_company_data(soup):
    companies = []
    listings = soup.select(".listing-card")

    if not listings:
        print("⚠️ No listings found on page.")
        return []

    for item in listings[:MAX_COMPANIES_PER_PAGE]:
        name_tag = item.select_one(".listing-card__title a")
        clutch_profile = f"https://themanifest.com{name_tag.get('href')}" if name_tag else None

        website_tag = item.select_one(".company-details__visit-website a")
        website = website_tag.get("href") if website_tag else None

        location_tag = item.select_one(".listing-card__location")
        location = location_tag.text.strip() if location_tag else None

        employee_range_tag = item.find(string=lambda text: "Employees" in text)
        employees = employee_range_tag.strip() if employee_range_tag else None

        founded_tag = item.find(string=lambda text: "Founded" in text)
        founded = founded_tag.strip() if founded_tag else None

        record = {
            "Website": website,
            "Clutch Profile": clutch_profile,
            "Location": location,
            "Employee Range": employees,
            "founded": founded
        }

        if website:  # Save only if website exists
            companies.append(record)

    return companies

def upload_to_airtable(records):
    for record in records:
        try:
            table.create(record)
            print(f"✅ Uploaded: {record.get('Clutch Profile')}")
        except Exception as e:
            print(f"❌ Failed to upload record: {e}")

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
