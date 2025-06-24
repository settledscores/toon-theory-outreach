import os
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME)

BASE_URL = "https://www.goodfirms.co/business-services/accounting/usa"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape_page(url):
    print(f"🌐 Scraping: {url}")
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"❌ Failed to fetch: {url} (status {res.status_code})")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    listings = soup.select("div.company-info")[:5]

    results = []
    for listing in listings:
        name_tag = listing.select_one("h3 a")
        profile_url = "https://www.goodfirms.co" + name_tag["href"] if name_tag else None
        name = name_tag.text.strip() if name_tag else None

        website_tag = listing.find_next("a", class_="visit-website ga-url")
        website = website_tag["href"] if website_tag and "href" in website_tag.attrs else None

        tagline_tag = listing.select_one(".company-intro")
        tagline = tagline_tag.text.strip() if tagline_tag else None

        record = {
            "name": name,
            "profile_url": profile_url,
            "website": website,
            "tagline": tagline,
        }

        print(f"➡️ Found: {name} | {website}")
        results.append(record)

    return results

def upload_to_airtable(companies):
    for company in companies:
        table.create(company)
        print(f"✅ Uploaded: {company['name']}")

def main():
    print("🔄 Starting GoodFirms scraper...")
    all_results = []
    for page in range(2):  # Page 0 and 1
        url = f"{BASE_URL}?page={page}"
        all_results.extend(scrape_page(url))

    if all_results:
        upload_to_airtable(all_results)
    else:
        print("⚠️ No listings extracted.")

    print("🎉 Scraping complete.")

if __name__ == "__main__":
    main()
