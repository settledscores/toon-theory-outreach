import time
from playwright.sync_api import sync_playwright

BBB_SEARCH_URL = "https://www.bbb.org/search?find_country=USA&find_entity=60005-101&find_id=1_100&find_latlng=30.314613%2C-97.793745&find_loc=Austin%2C%20TX&find_text=Accounting&find_type=Category&page=1&sort=Relevance"

def get_profile_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("🚯 Launching Playwright to fetch BBB search results...")
        page.goto(BBB_SEARCH_URL, timeout=60000)

        print("⏳ Waiting for full page load (networkidle)...")
        page.wait_for_load_state("networkidle")

        print("⏳ Sleeping to bypass Cloudflare...")
        time.sleep(10)  # Let JavaScript finish rendering

        print("🛃 Scrolling to force lazy loading...")
        for i in range(0, 3000, 500):
            page.evaluate(f"window.scrollTo(0, {i})")
            time.sleep(1)

        html_content = page.content()
        with open("bbb_debug_final.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("📄 Saved final HTML for inspection: bbb_debug_final.html")

        links = page.locator("a[href*='/profile/']")
        found = links.count()
        print(f"🔗 Found {found} profile links")

        profile_urls = []
        for i in range(min(found, 5)):
            href = links.nth(i).get_attribute("href")
            if href:
                profile_urls.append("https://www.bbb.org" + href)

        browser.close()
        return profile_urls


def main():
    print("🔄 Starting full BBB scrape...")
    links = get_profile_links()
    print("\n".join(links))
    print("\n🌝 Done.")

if __name__ == "__main__":
    main()
