import os
import time
import requests
from bs4 import BeautifulSoup

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

CURLIE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CurlieScraper/1.0)"
}

BASE_URL_TEMPLATE = "https://curlie.org/en/Business/Accounting/Firms/Accountants/North_America/United_States/{}"
MAX_PER_STATE = 5
REQUEST_DELAY = 3  # seconds between requests


US_STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New_Hampshire",
    "New_Jersey", "New_Mexico", "New_York", "North_Carolina", "North_Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode_Island", "South_Carolina", "South_Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West_Virginia",
    "Wisconsin", "Wyoming"
]


def scrape_state(state):
    url = BASE_URL_TEMPLATE.format(state)
    print(f"🔍 Scraping {state}: {url}")
    try:
        res = requests.get(url, headers=CURLIE_HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to load {state}: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    entries = soup.select("div.site-item")
    leads = []

    for entry in entries:
        if len(leads) >= MAX_PER_STATE:
            break

        name_tag = entry.select_one(".site-title")
        link_tag = name_tag.find("a") if name_tag else None
        description_tag = entry.select_one(".site-descr")

        if not name_tag or not link_tag:
            continue

        name = name_tag.text.strip()
        website = link_tag.get("href")
        notes = description_tag.text.strip() if description_tag else ""
        location = state.replace("_", " ") + ", US"

        if not website.startswith("http"):
            continue

        leads.append({
            "business name": name,
            "website url": website,
            "notes": notes,
            "location": location
        })

    return leads


def push_to_airtable(record):
    payload = {
        "fields": {
            "business name": record["business name"],
            "website url": record["website url"],
            "notes": record["notes"],
            "location": record["location"]
        }
    }

    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    try:
        res = requests.post(url, headers=AIRTABLE_HEADERS, json=payload)
        res.raise_for_status()
        print(f"✅ Uploaded: {record['business name']} ({record['location']})")
    except requests.RequestException as e:
        print(f"❌ Failed to upload {record['business name']}: {e}")


if __name__ == "__main__":
    for state in US_STATES:
        leads = scrape_state(state)
        for lead in leads:
            push_to_airtable(lead)
            time.sleep(REQUEST_DELAY)
