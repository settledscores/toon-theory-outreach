import os
import time
import asyncio
from pyairtable import Api
from playwright.async_api import async_playwright

# Airtable config
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
table = Api(AIRTABLE_API_KEY).base(AIRTABLE_BASE_ID).table(SCRAPER_TABLE_NAME)

# Constants
BASE_URL = "https://themanifest.com/business-consulting/firms?page={}"
MAX_PAGES = 2
MAX_COMPANIES = 5
WAIT_TIME = 60  # seconds

async def scrape_manifest():
    print("🔄 Starting Manifest scraper (Playwright)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for i in range(MAX_PAGES):
            url = BASE_URL.format(i)
            print(f"🌐 Scraping: {url}")
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state("networkidle")

            html = await page.content()

            # Save raw HTML in Airtable
            try:
                table.create({
                    "Raw HTML": html[:100000],  # Airtable field limit safety
                    "Notes": f"Page {i} snapshot",
                })
                print(f"✅ Uploaded page {i} HTML to Airtable.")
            except Exception as e:
                print(f"❌ Failed to upload HTML: {e}")

            # Scrape company blocks
            company_cards = await page.query_selector_all(".directory-list__item")  # each company card

            for card in company_cards[:MAX_COMPANIES]:
                try:
                    title_el = await card.query_selector("h3 a")
                    company_name = await title_el.inner_text() if title_el else None
                    profile_link = await title_el.get_attribute("href") if title_el else None
                    profile_link = "https://themanifest.com" + profile_link if profile_link else None

                    website_el = await card.query_selector("a.link--external")
                    website = await website_el.get_attribute("href") if website_el else None

                    location_el = await card.query_selector(".location")
                    location = await location_el.inner_text() if location_el else None

                    services_el = await card.query_selector(".tag-list")
                    service_breakdown = await services_el.inner_text() if services_el else None

                    founded_el = await card.query_selector(".profile-meta")
                    founded_text = await founded_el.inner_text() if founded_el else ""
                    founded_year = None
                    for token in founded_text.split():
                        if token.isdigit() and len(token) == 4:
                            founded_year = token
                            break

                    data = {
                        "Website": website,
                        "Clutch Profile": profile_link,
                        "Location": location,
                        "service breakdown": service_breakdown,
                        "founded": founded_year,
                    }

                    table.create(data)
                    print(f"✅ Uploaded: {company_name}")
                except Exception as e:
                    print(f"❌ Company parse error: {e}")

            await asyncio.sleep(WAIT_TIME)

        await browser.close()
        print("🎉 Scraper finished.")

if __name__ == "__main__":
    asyncio.run(scrape_manifest())
