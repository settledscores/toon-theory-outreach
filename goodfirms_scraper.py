import os
import random
import requests
from bs4 import BeautifulSoup
from pyairtable import Table
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

BASE_URL = "https://www.goodfirms.co/business-services/accounting/usa?page={}"
PLATFORM = "GoodFirms"

table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME)

def scrape_page(page_num):
    url = BASE_URL.format(page_num)
    print(f"🌐 Scraping: {url}")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to fetch: {url} (status {response.status_code})")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.select(".company-list .company-content")

        leads = []
        for listing in listings:
            name_tag = listing.select_one(".profile-title a")
            website_tag = listing.select_one(".visit-website a")
            desc_tag = listing.select_one(".company-info p")

            if name_tag and website_tag:
                leads.append({
                    "company name": name_tag.get_text(strip=True),
                    "website url": website_tag["href"],
                    "description": desc_tag.get_text(strip=True) if desc_tag else "",
                    "platform": PLATFORM
                })

        return leads

    except Exception as e:
        print(f"❌ Exception while scraping: {e}")
        return []

def main():
    print("🔄 Starting GoodFirms scraper...")
    all_leads = []

    for page in range(2):  # pages 0 and 1
        page_leads = scrape_page(page)
        if page_leads:
            selected = random.sample(page_leads, min(5, len(page_leads)))
            all_leads.extend(selected)

    if all_leads:
        for lead in all_leads:
            try:
                table.create(lead)
            except Exception as e:
                print(f"❌ Failed to push to Airtable: {e}")
    else:
        print("⚠️ No listings extracted.")

    print("🎉 Scraping complete.")

if __name__ == "__main__":
    main()
