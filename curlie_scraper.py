# curlie_general_scraper.py
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# ▶️ Airtable credentials (from your repo/runner secrets)
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID          = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME       = os.getenv("SCRAPER_TABLE_NAME")

AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type":  "application/json"
}

CURLIE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CurlieScraper/1.2)"
}

REQUEST_DELAY_SEC = 3        # → ~20 requests/min
MAX_RESULTS_PAGE  = 5        # we’ll still collect everything, but throttle pushes

TARGET_URLS = [
    "https://curlie.org/en/Business/International_Business_and_Trade/Consulting/Business_Development",
    "https://curlie.org/en/Business/Human_Resources/Outsourcing",
    "https://curlie.org/en/Business/Human_Resources/Recruiting_and_Retention",
    "https://curlie.org/en/Business/Human_Resources/Consulting/",
    "https://curlie.org/en/Business/Financial_Services/Financial_Consultants",
    "https://curlie.org/Society/Law/Employment/Legal_Recruiters/"
]

# ──────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────
US_STATES = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
    "Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
    "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan",
    "Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire",
    "New Jersey","New Mexico","New York","North Carolina","North Dakota","Ohio",
    "Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina","South Dakota",
    "Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia",
    "Wisconsin","Wyoming"
]
MAJOR_CITIES = [
    "London","Toronto","Vancouver","Berlin","Sydney","Melbourne","Paris","Zurich",
    "Dublin","Singapore","Dubai","Tokyo","Hong Kong","Barcelona","Madrid","Munich",
    "Frankfurt","Copenhagen","Stockholm","Oslo","Helsinki","Amsterdam","Brussels"
]

def infer_location(text: str) -> str:
    """Return a clean location like 'Texas, US' or 'London' or ''."""
    # check US states first
    for state in US_STATES:
        if re.search(rf"\b{re.escape(state)}\b", text, flags=re.IGNORECASE):
            return f"{state}, US"
    # then major world cities
    for city in MAJOR_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", text, flags=re.IGNORECASE):
            return city
    return ""

def infer_industry(source_url: str, notes: str) -> str:
    path = urlparse(source_url).path.lower()
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

# ──────────────────────────────────────────────────────────────
#  Scraper core
# ──────────────────────────────────────────────────────────────
def scrape_curlie_url(base_url: str) -> list[dict]:
    leads, page_url = [], base_url
    while page_url:
        print(f"🔍  Scraping {page_url}")
        try:
            res = requests.get(page_url, headers=CURLIE_HEADERS, timeout=10)
            res.raise_for_status()
        except Exception as exc:
            print(f"❌ Failed to load {page_url}: {exc}")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        for entry in soup.select("div.site-item"):
            name_tag  = entry.select_one(".site-title")
            link_tag  = name_tag.find("a") if name_tag else None
            notes_tag = entry.select_one(".site-descr")
            if not (name_tag and link_tag):                      # skip bad nodes
                continue

            name   = name_tag.text.strip()
            site   = link_tag.get("href")
            notes  = notes_tag.text.strip() if notes_tag else ""
            if not site.startswith("http"):
                continue

            leads.append({
                "business name": name,
                "website url"  : site,
                "notes"        : notes,
                "location"     : infer_location(notes),
                "industry"     : infer_industry(base_url, notes)
            })

        # pagination
        next_link = soup.find("a", string="Next »")
        page_url  = f"https://curlie.org{next_link['href']}" if next_link and next_link.get("href") else None
        if page_url:
            time.sleep(REQUEST_DELAY_SEC)
    return leads

# ──────────────────────────────────────────────────────────────
#  Airtable push
# ──────────────────────────────────────────────────────────────
def push_airtable(record: dict) -> None:
    payload = {"fields": record}
    url     = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    try:
        r = requests.post(url, headers=AIRTABLE_HEADERS, json=payload, timeout=10)
        r.raise_for_status()
        print(f"✅ Uploaded: {record['business name']}")
    except requests.RequestException as exc:
        print(f"❌ Upload failed for {record['business name']}: {exc}")

# ──────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for src in TARGET_URLS:
        for rec in scrape_curlie_url(src):
            push_airtable(rec)
            time.sleep(REQUEST_DELAY_SEC)
