import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import fs
from datetime import datetime

# Paths
SCRAPED_LEADS_PATH = "toon-theory-outreach/leads/scraped_leads.json"
WEB_COPY_PATH = "toon-theory-outreach/leads/web_copy.json"

# Settings
MAX_PAGES = 15
MAX_TEXT_LENGTH = 10000
MIN_WORDS_THRESHOLD = 50

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ToonTheoryBot/1.0; +https://toontheory.com)"
}

def clean_text(text):
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return " ".join(text.split())

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "svg", "img", "noscript", "aside"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

def normalize_url(url):
    url = url.strip().rstrip("/")
    return url if url.startswith("http") else f"https://{url}"

def crawl_site(base_url, max_pages=MAX_PAGES):
    visited = set()
    to_visit = [base_url]
    domain = urlparse(base_url).netloc
    all_text = ""

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                visited.add(url)
                soup = BeautifulSoup(res.text, "html.parser")
                visible_text = extract_visible_text(res.text)
                all_text += visible_text + " "

                for link in soup.find_all("a", href=True):
                    href = urljoin(url, link["href"])
                    if urlparse(href).netloc == domain and href not in visited:
                        to_visit.append(href)
        except Exception as e:
            print(f"⚠️ Failed to fetch {url}: {e}")
            continue

    return clean_text(all_text)

def main():
    if not os.path.exists(SCRAPED_LEADS_PATH):
        print(f"❌ Missing input file: {SCRAPED_LEADS_PATH}")
        return

    os.makedirs(os.path.dirname(WEB_COPY_PATH), exist_ok=True)

    with open(SCRAPED_LEADS_PATH, "r", encoding="utf-8") as f:
        leads_data = json.load(f)

    try:
        with open(WEB_COPY_PATH, "r", encoding="utf-8") as f:
            existing_records = json.load(f).get("records", [])
    except:
        existing_records = []

    existing_urls = set(r["website url"].strip().lower() for r in existing_records)
    updated_records = existing_records[:]

    for lead in leads_data.get("records", []):
        website = lead.get("website url", "").strip().lower()
        if not website or website in existing_urls:
            continue

        norm_url = normalize_url(website)
        print(f"🌐 Crawling site: {norm_url}")

        content = crawl_site(norm_url)
        if len(content.split()) < MIN_WORDS_THRESHOLD:
            print("⚠️ Skipping — not enough content.")
            continue

        trimmed = content[:MAX_TEXT_LENGTH]

        updated = {**lead, "web copy": trimmed}
        updated_records.append(updated)
        existing_urls.add(website)
        print(f"✅ Scraped web content for {urlparse(norm_url).netloc}")

    output = {
        "scraped_at": datetime.utcnow().isoformat(),
        "total": len(updated_records),
        "records": updated_records
    }

    with open(WEB_COPY_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n📝 Saved web copy for {len(updated_records)} businesses → {WEB_COPY_PATH}")

if __name__ == "__main__":
    main()
