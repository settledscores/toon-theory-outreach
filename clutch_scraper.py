import time
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
import os

# Airtable setup using GitHub secrets
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
table = api.base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

# ScraperAPI setup
SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")
BASE_URL = "https://clutch.co/hr"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Configuration
MAX_PAGES = 2
MAX_COMPANIES_PER_PAGE = 5

def fetch_with_scraperapi(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        response = requests.get(proxy_url, headers=HEADERS)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ Failed to fetch: {url} (status {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Exception fetching {url}: {e}")
        return None

def extract_company_data(soup):
    companies = []
    listings = soup.select(".provider-info")

    for item in listings[:MAX_COMPANIES_PER_PAGE]:
        name_tag = item.select_one(".company_title a")
        if not name_tag:
            continue

        clutch_profile = f"https://clutch.co{name_tag.get('href')}"
        website_tag = item.select_one(".website-link__item a")
        website = website_tag.get("href") if website_tag else None

        location_tag = item.select_one(".locality")
        location = location_tag.text.strip() if location_tag else None

        employees = None
        for li in item.select(".list-item"):
            if "Employees" in li.text:
                employees = li.text.replace("Employees: ", "").strip()

        service_tag = item.select_one(".chart-label")
        service_breakdown = service_tag.text.strip() if service_tag else None

        companies.append({
            "Website": website,
            "Clutch Profile": clutch_profile,
            "Location": location,
            "Employee Range": employees,
            "service breakdown": service_breakdown,
        })

    return companies

def upload_to_airtable(records):
    for record in records:
        try:
            table.create(record)
            print(f"✅ Uploaded: {record.get('Clutch Profile')}")
        except Exception as e:
            print(f"❌ Upload failed: {e}")

def main():
    print("🔄 Starting Clutch scraper...")
    for page in range(MAX_PAGES):
        url = f"{BASE_URL}?page={page}"
        print(f"🌐 Scraping: {url}")
        html = fetch_with_scraperapi(url)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            companies = extract_company_data(soup)
            if companies:
                upload_to_airtable(companies)
        time.sleep(60)  # Rate limiting

    print("🎉 Scraper finished.")

if __name__ == "__main__":
    main()
