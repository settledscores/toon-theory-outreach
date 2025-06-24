import os
import requests
from bs4 import BeautifulSoup

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

CURLIE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CurlieScraper/1.0)"
}

MAX_RESULTS = 4  # Test run limit


def scrape_curlie_page(url, limit=MAX_RESULTS):
    print(f"🔍 Scraping: {url}")
    try:
        response = requests.get(url, headers=CURLIE_HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    entries = soup.select("div.site-item")
    for entry in entries:
        if len(results) >= limit:
            break

        name_tag = entry.select_one(".site-title")
        link_tag = entry.select_one(".site-title > a")

        if not name_tag or not link_tag:
            continue

        name = name_tag.text.strip()
        website_url = link_tag.get("href")

        if not website_url.startswith("http"):
            continue

        results.append({
            "business name": name,
            "website url": website_url
        })

    return results


def push_to_airtable(data):
    if not data:
        print("⚠️ No data to push.")
        return

    for record in data:
        payload = {
            "fields": {
                "business name": record["business name"],
                "website url": record["website url"]
            }
        }

        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
        try:
            res = requests.post(url, headers=HEADERS, json=payload)
            res.raise_for_status()
            print(f"✅ Uploaded: {record['business name']}")
            print("🪵 Response:", res.json())  # <-- Debug response from Airtable
        except requests.RequestException as e:
            print(f"❌ Failed to upload {record['business name']}: {e}")


if __name__ == "__main__":
    test_url = "https://curlie.org/Business/Accounting/Firms/Accountants/North_America/United_States/California/"
    data = scrape_curlie_page(test_url)
    push_to_airtable(data)
