import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

CURLIE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CurlieScraper/1.1)"
}

MAX_RESULTS_PER_PAGE = 5
REQUEST_DELAY = 3


TARGET_URLS = [
    "https://curlie.org/en/Business/International_Business_and_Trade/Consulting/Business_Development",
    "https://curlie.org/en/Business/Human_Resources/Outsourcing",
    "https://curlie.org/en/Business/Human_Resources/Recruiting_and_Retention",
    "https://curlie.org/en/Business/Human_Resources/Consulting/",
    "https://curlie.org/en/Business/Financial_Services/Financial_Consultants",
    "https://curlie.org/Society/Law/Employment/Legal_Recruiters/"
]


def infer_location(text):
    match = re.search(r"\b([A-Z][a-z]+(?:,\s?[A-Z]{2})?)\b", text)
    if match:
        return match.group(1) + ", US" if len(match.group(1)) <= 20 else match.group(1)
    return ""


def infer_industry(url, notes):
    path = urlparse(url).path.lower()
    if "human_resources" in path:
        return "HR"
    if "financial" in path:
        return "Financial Consulting"
    if "legal" in path or "law" in path:
        return "Legal"
    if "business_development" in path:
        return "Business Development"
    if "consulting" in path:
        return "Consulting"
    return "Unknown"


def scrape_curlie_url(base_url):
    all_leads = []
    page_url = base_url

    while page_url:
        print(f"🔍 Scraping: {page_url}")
        try:
            res = requests.get(page_url, headers=CURLIE_HEADERS, timeout=10)
            res.raise_for_status()
        except Exception as e:
            print(f"❌ Failed to fetch {page_url}: {e}")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        entries = soup.select("div.site-item")

        for entry in entries:
            name_tag = entry.select_one(".site-title")
            link_tag = name_tag.find("a") if name_tag else None
            description_tag = entry.select_one(".site-descr")

            if not name_tag or not link_tag:
                continue

            name = name_tag.text.strip()
            website = link_tag.get("href")
            notes = description_tag.text.strip() if description_tag else ""
            location = infer_location(notes)
            industry = infer_industry(base_url, notes)

            if not website.startswith("http"):
                continue

            all_leads.append({
                "business name": name,
                "website url": website,
                "notes": notes,
                "location": location,
                "industry": industry
            })

        # Look for "Next »"
        next_link = soup.find("a", string="Next »")
        if next_link and next_link.get("href"):
            page_url = "https://curlie.org" + next_link["href"]
            time.sleep(REQUEST_DELAY)
        else:
            break

    return all_leads


def push_to_airtable(record):
    payload = {
        "fields": {
            "business name": record["business name"],
            "website url": record["website url"],
            "notes": record["notes"],
            "location": record["location"],
            "industry": record["industry"]
        }
    }

    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    try:
        res = requests.post(url, headers=AIRTABLE_HEADERS, json=payload)
        res.raise_for_status()
        print(f"✅ Uploaded: {record['business name']}")
    except requests.RequestException as e:
        print(f"❌ Failed to upload {record['business name']}: {e}")


if __name__ == "__main__":
    for source_url in TARGET_URLS:
        leads = scrape_curlie_url(source_url)
        for record in leads:
            push_to_airtable(record)
            time.sleep(REQUEST_DELAY)
