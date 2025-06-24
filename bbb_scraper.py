import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME, AIRTABLE_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1; +https://example.com/bot)"
}

BASE_URL = "https://www.bbb.org"
SEARCH_URL = "https://www.bbb.org/search?find_country=USA&find_entity=60005-101&find_id=1_100&find_latlng=30.314613%2C-97.793745&find_loc=Austin%2C%20TX&find_text=Accounting&find_type=Category&page=1&sort=Relevance"

MAX_LEADS = 5
REQUEST_INTERVAL = 3  # seconds

def get_search_results():
    print("🔍 Requesting BBB search page with ScraperAPI...")
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": SEARCH_URL,
        "render": "true"
    }
    try:
        res = requests.get("http://api.scraperapi.com", params=params, headers=HEADERS, timeout=30)
        print(f"📄 Response size: {len(res.text)} bytes")
        soup = BeautifulSoup(res.text, 'html.parser')
        links = soup.select("a.Link__StyledLink-sc-1dh2vhu-0")
        profile_urls = [urljoin(BASE_URL, link['href']) for link in links if "/profile/" in link['href']]
        print(f"🔗 Found {len(profile_urls)} profile links")
        return profile_urls[:MAX_LEADS]
    except Exception as e:
        print(f"❌ Failed to fetch search results: {e}")
        return []

def scrape_profile(url):
    print(f"➡️ Scraping profile: {url}")
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')

        business_name = soup.select_one("h1[class*=Heading__HeadingStyled]")
        website_url = soup.find("a", string="Visit Website")
        notes = soup.select_one("section p")
        location = soup.select_one("address")
        years = soup.find(text=lambda t: t and "years in business" in t.lower())

        decision_section = soup.find("h2", string=lambda s: s and "Business Management" in s)
        name, title = "", ""
        if decision_section:
            li = decision_section.find_next("li")
            if li:
                parts = list(li.stripped_strings)
                if len(parts) >= 2:
                    name, title = parts[0], parts[1]
                elif len(parts) == 1:
                    name = parts[0]

        fields = {
            "website url": website_url['href'] if website_url else "",
            "notes": notes.text.strip() if notes else "",
            "location": location.text.strip() + ", US" if location else "Austin, US",
            "industry": "Accounting",
            "years": years.strip() if years else "",
            "Decision Maker Name": name,
            "Decision Maker Title": title
        }

        print(f"📦 Extracted fields: {fields}")
        airtable.insert(fields)
        print(f"✅ Uploaded to Airtable: {fields['website url']}")

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")

def main():
    print("🔄 Starting BBB scraper...")
    profile_links = get_search_results()
    print("🚀 Starting profile scrape...\n")

    for url in profile_links:
        scrape_profile(url)
        time.sleep(REQUEST_INTERVAL)

    print("🏁 Done.")

if __name__ == "__main__":
    main()
