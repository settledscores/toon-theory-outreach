import os
import time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SEARCH_URL = "https://www.bbb.org/search?find_country=USA&find_entity=60005-101&find_id=1_100&find_latlng=30.314613%2C-97.793745&find_loc=Austin%2C%20TX&find_text=Accounting&find_type=Category&page=1&sort=Relevance"
DEBUG_FILE = "bbb_debug_final.html"


def get_profile_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🧭 Launching Playwright to fetch BBB search results...")
        page.goto(SEARCH_URL, timeout=60000)

        print("⏳ Waiting manually for JS content to hydrate...")
        time.sleep(10)

        print("⬇️ Scrolling page gradually to trigger lazy load...")
        for i in range(0, 4000, 400):
            page.evaluate(f"window.scrollTo(0, {i})")
            time.sleep(0.8)

        print("📄 Saving hydrated HTML to debug file...")
        html = page.content()
        Path(DEBUG_FILE).write_text(html)

        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.select("a[href*='/profile/']"):
            href = a.get("href")
            if href and href.startswith("/profile/"):
                full_url = f"https://www.bbb.org{href}"
                if full_url not in links:
                    links.append(full_url)

        print(f"🔗 Found {len(links)} profile links")
        return links[:5]  # For test run only


def scrape_profile(url):
    print(f"🔍 Visiting profile: {url}")
    # Future: Implement actual profile scraping
    return {
        "website url": url,
        "notes": "Placeholder",
        "location": "Austin, TX, US",
        "industry": "Accounting",
        "years": "",
        "Decision Maker Name": "",
        "Decision Maker Title": "",
        "Email Permutations": ""
    }


def main():
    print("🔄 Starting full BBB scrape...")
    links = get_profile_links()

    print("🚀 Starting profile scrape...")
    for link in links:
        record = scrape_profile(link)
        print(f"✅ Record scraped: {record['website url']}")

    print("\n🏁 Done.")


if __name__ == "__main__":
    main()
