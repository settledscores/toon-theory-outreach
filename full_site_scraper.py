import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("BASEROW_API_KEY")
TABLE_ID = os.getenv("BASEROW_OUTREACH_TABLE")
BASE_URL = f"https://api.baserow.io/api/database/rows/table/{TABLE_ID}"
HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

CRAWL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ToonTheoryBot/1.0; +https://toontheory.com)"
}

MAX_TEXT_LENGTH = 10000
MIN_WORDS_THRESHOLD = 50

def fetch_records():
    res = requests.get(BASE_URL + "?user_field_names=true", headers=HEADERS)
    res.raise_for_status()
    return res.json()["results"]

def update_record(record_id, payload):
    res = requests.patch(f"{BASE_URL}/{record_id}/", headers=HEADERS, json=payload)
    res.raise_for_status()

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

def crawl_site(base_url, max_pages=15):
    visited = set()
    to_visit = [base_url]
    domain = urlparse(base_url).netloc
    all_text = ""

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        try:
            res = requests.get(url, headers=CRAWL_HEADERS, timeout=10)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                visited.add(url)
                print(f"🕷️ Crawling: {url}")
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
    records = fetch_records()
    updated_count = 0

    for record in records:
        record_id = record["id"]
        website = record.get("website", "").strip()
        existing_copy = record.get("web copy", "").strip()

        if not website or existing_copy:
            continue

        norm_url = normalize_url(website)
        print(f"\n🌐 Starting crawl for: {norm_url}")
        content = crawl_site(norm_url)

        if len(content.split()) < MIN_WORDS_THRESHOLD:
            print(f"⚠️ Skipping — not enough meaningful text.")
            continue

        trimmed = content[:MAX_TEXT_LENGTH]
        try:
            update_record(record_id, {"web copy": trimmed})
            print(f"✅ Updated: {website}")
            updated_count += 1
        except Exception as e:
            print(f"❌ Failed to update: {website} — {e}")

    print(f"\n🏁 Done. {updated_count} sites updated.")

if __name__ == "__main__":
    main()
