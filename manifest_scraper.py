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
SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")  # Reuse this secret
BASE_URL = "https://themanifest.com/business-consulting/firms"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Scrape limits
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
        print(f"❌ Exception for {url}: {e}")
        return None

def extract_company_data(soup):
    companies = []
    listings = soup.select(".listing-card")

    for item in listings[:MAX_COMPANIES_PER_PAGE]:
        profile_tag = item.select_one(".listing-card__title a")
        profile_url = f"https://themanifest.com{profile_tag.get('href')}" if profile_tag else None

        website_tag = item.select_one(".company-details__visit-website a")
        website = website_tag.get("href") if website_tag else None

        location_tag = item.select_one(".location-card")
        location = location_tag.get_text(strip=True) if location_tag else None

        employee_range = None
        founded_year = None
        breakdown = []

        for info in item.select(".listing-card__info li"):
            text = info.get_text(strip=True)
            if "Employees" in text:
                employee_range = text.split("Employees:")[-1].strip()
            elif "Founded" in text:
                founded_year = text.split("Founded:")[-1].strip()
            else:
                breakdown.append(text)

        record = {
            "Website": website,
            "Clutch Profile": profile_url,
            "Location": location,
            "Employee Range": employee_range,
            "founded": founded_year,
            "service breakdown": ", ".join(breakdown),
        }
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
        time.sleep(60)  # 1 request/min rate limit

    print("🎉 Done.")

if __name__ == "__main__":
    main()
    
