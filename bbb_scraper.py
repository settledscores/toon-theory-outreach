import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv
from airtable import Airtable
from playwright.sync_api import sync_playwright

# Load environment
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

airtable = Airtable(AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME, AIRTABLE_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1; +https://example.com/bot)"
}

BASE_URL = "https://www.bbb.org"
SEARCH_URL = "https://www.bbb.org/search?find_country=USA&find_entity=60005-101&find_id=1_100&find_latlng=30.314613%2C-97.793745&find_loc=Austin%2C%20TX&find_text=Accounting&find_type=Category&page=1&sort=Relevance"

MAX_LEADS = 5
WAIT_BETWEEN = 3  # seconds


def get_profile_links():
    print("🧭 Launching Playwright to fetch BBB search results...")
    links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(SEARCH_URL, timeout=60000)

        try:
            print("⏳ Waiting for profile links...")
            page.wait_for_selector("a[href*='/profile/']", timeout=25000)
            profile_elements = page.query_selector_all("a[href*='/profile/']")
        except Exception as e:
            print(f"⚠️ Selector wait failed: {e}")
            try:
                html = page.content()
                print(f"📁 Current working dir: {os.getcwd()}")
                with open("bbb_debug.html", "w", encoding="utf-8") as f:
                    f.write(html)
                    f.flush()
                    os.fsync(f.fileno())
                print("📄 Saved fallback HTML to bbb_debug.html")
            except Exception as write_err:
                print(f"❌ Failed to write debug HTML: {write_err}")
            browser.close()
            return []

        for el in profile_elements:
            href = el.get_attribute("href")
            if href and "/profile/" in href:
                full_url = urljoin(BASE_URL, href)
                if full_url not in links:
                    links.append(full_url)

        browser.close()

    print(f"🔗 Extracted {len(links)} profile links.")
    return links[:MAX_LEADS]


def scrape_profile(url):
    print(f"➡️ Scraping profile: {url}")
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')

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
        print(f"❌ Failed scraping {url}: {e}")


def main():
    print("🔄 Starting full BBB scrape...")
    links = get_profile_links()

    for url in links:
        scrape_profile(url)
        time.sleep(WAIT_BETWEEN)

    print("🏁 Done.")


if __name__ == "__main__":
    main()
