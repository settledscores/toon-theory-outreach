import os
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Path
SCRAPED_LEADS_PATH = "leads/scraped_leads.json"

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
        print(f"❌ Missing file: {SCRAPED_LEADS_PATH}")
        return

    with open(SCRAPED_LEADS_PATH, "r", encoding="utf-8") as f:
        leads = json.load(f)

    updated = []
    changed = False

    for lead in leads.get("records", []):
        website = lead.get("website url", "").strip()
        web_copy = lead.get("web copy", "").strip()

        if not website or web_copy:
            updated.append(lead)
            continue

        norm_url = normalize_url(website)
        print(f"🌐 Crawling site: {norm_url}")

        content = crawl_site(norm_url)
        if len(content.split()) < MIN_WORDS_THRESHOLD:
            print("⚠️ Skipping — not enough content.")
            updated.append(lead)
            continue

        trimmed = content[:MAX_TEXT_LENGTH]
        lead["web copy"] = trimmed
        updated.append(lead)
        changed = True
        print(f"✅ Scraped web content for {urlparse(norm_url).netloc}")

    if changed:
        output = {
            "scraped_at": datetime.utcnow().isoformat(),
            "total": len(updated),
            "records": updated
        }

        with open(SCRAPED_LEADS_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        print(f"\n📝 Updated web copy in {SCRAPED_LEADS_PATH}")
    else:
        print("⚠️ No new web copy to update.")

if __name__ == "__main__":
    main()
