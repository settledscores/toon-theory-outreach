import os
import time
import requests
from bs4 import BeautifulSoup
from pyairtable import Table
from datetime import datetime

SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

SCRAPER_API_URL = "http://api.scraperapi.com"
HEADERS = {"Content-Type": "application/json"}

# Airtable table instance
table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME)

def fetch_page(url):
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "render": "true"
    }
    response = requests.get(SCRAPER_API_URL, params=params, headers=HEADERS)
    if response.status_code == 200:
        return response.text
    else:
        print(f"❌ Failed to fetch: {url} (status {response.status_code})")
        return None

def parse_company_cards(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(".provider-info")
    companies = []
    for card in cards[:5]:  # Only extract 5 per page for now
        try:
            name_tag = card.select_one("h3 a")
            clutch_profile = "https://clutch.co" + name_tag["href"] if name_tag else None
            website_tag = card.select_one(".website-link__item a")
            website = website_tag["href"] if website_tag else None
            
            employee_range = None
            location = None
            service_breakdown = None
            
            meta_tags = card.select(".list-key-dots li")
            for tag in meta_tags:
                text = tag.get_text(strip=True)
                if "Employees" in text:
                    employee_range = text.replace("Employees:", "").strip()
                elif "Location" in text:
                    location = text.replace("Location:", "").strip()
            
            # Example placeholder until we implement internal profile scanning
            service_breakdown = "unknown"

            companies.append({
                "Website": website,
                "Clutch Profile": clutch_profile,
                "Employee Range": employee_range,
                "Location": location,
                "founded": "unknown",
                "service breakdown": service_breakdown,
                "Date Added": datetime.utcnow().isoformat(),
                "Email Source": "Clutch.co",
                "Status": "new"
            })
        except Exception as e:
            print(f"⚠️ Error parsing company card: {e}")
            continue
    return companies

def upload_to_airtable(records):
    for record in records:
        try:
            table.create(record)
            print(f"✅ Uploaded: {record.get('Clutch Profile')}")
        except Exception as e:
            print(f"❌ Airtable upload error: {e}")

if __name__ == "__main__":
    for page in range(2):
        url = f"https://clutch.co/hr?page={page}"
        print(f"🌐 Scraping: {url}")
        html = fetch_page(url)
        if html:
            records = parse_company_cards(html)
            print(f"📈 Companies extracted: {len(records)}")
            upload_to_airtable(records)
        time.sleep(60)  # Respectful delay
