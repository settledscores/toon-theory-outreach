import os
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from airtable import Airtable
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

START_URL = "https://www.bbb.org/search?find_country=USA&find_entity=60005-101&find_id=1_100&find_latlng=30.314613%2C-97.793745&find_loc=Austin%2C%20TX&find_text=Accounting&find_type=Category&page=1&sort=Relevance"

def get_profile_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("🔄 Starting full BBB scrape...")
        print("🧭 Launching Playwright to fetch BBB search results...")
        page.goto(START_URL, timeout=60000)
        try:
            print("⏳ Waiting for profile links...")
            page.wait_for_selector("a[href*='/profile/']", timeout=25000)
        except Exception as e:
            print(f"⚠️ Selector wait failed: {e}")
        
        html = page.content()
        
        # Log working dir and save fallback HTML
        cwd = os.getcwd()
        print(f"📁 Current working dir: {cwd}")
        debug_path = os.path.join(cwd, "bbb_debug.html")
        try:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"📄 Saved fallback HTML to {debug_path}")
        except Exception as e:
            print(f"❌ Failed to save debug.html: {e}")
        
        soup = BeautifulSoup(html, "html.parser")
        links = soup.select("a[href*='/profile/']")
        profile_urls = ["https://www.bbb.org" + a["href"] for a in links][:5]  # Just 5 for test
        browser.close()
        return profile_urls

def scrape_profile(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(5000)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        browser.close()

        def safe_select_text(selector):
            el = soup.select_one(selector)
            return el.get_text(strip=True) if el else ""

        website = safe_select_text("a[data-testid='business-website']")
        notes = safe_select_text("div[data-testid='business-profile-about']") or ""
        location = "Austin, TX, US"
        industry = "Accounting"
        years = safe_select_text("div:has(h4:contains('Years in Business')) span") or ""

        dm_name = safe_select_text("div[data-testid='principal-name']")
        dm_title = safe_select_text("div[data-testid='principal-role']")

        return {
            "website url": website,
            "notes": notes,
            "location": location,
            "industry": industry,
            "years": years,
            "Decision Maker Name": dm_name,
            "Decision Maker Title": dm_title,
        }

def main():
    links = get_profile_links()
    print(f"🔗 Found {len(links)} profile links")
    print("🚀 Starting profile scrape...")

    for link in links:
        try:
            record = scrape_profile(link)
            print(f"📦 Scraped: {record['website url']} - {record['Decision Maker Name']}")
            airtable.insert(record)
            time.sleep(2)  # Rate limit
        except Exception as e:
            print(f"❌ Error scraping {link}: {e}")

    print("\n🏁 Done.")

if __name__ == "__main__":
    main()
