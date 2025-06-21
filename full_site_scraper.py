import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from airtable import Airtable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Headers for crawling
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1; +https://example.com/bot)"
}

# Constants
MAX_TEXT_LENGTH = 10000
MIN_WORDS_THRESHOLD = 50

def clean_text(text):
    # Remove non-ASCII and excessive whitespace
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return " ".join(text.split())

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "svg", "img", "noscript", "aside"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

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
            res = requests.get(url, headers=HEADERS, timeout=10)
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

def normalize_url(url):
    url = url.strip().rstrip("/")
    return url if url.startswith("http") else f"https://{url}"

def main():
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website", "")
        web_copy = fields.get("web copy", "")

        if not website or web_copy:
            continue

        norm_url = normalize_url(website)
        print(f"\n🌐 Starting crawl for: {norm_url}")
        text = crawl_site(norm_url)

        if len(text.split()) < MIN_WORDS_THRESHOLD:
            print(f"⚠️ Skipping {norm_url} - not enough meaningful content.")
            continue

        trimmed_text = text[:MAX_TEXT_LENGTH]
        try:
            airtable.update(record["id"], {"web copy": trimmed_text})
            print(f"✅ Updated {website}")
            updated_count += 1
        except Exception as e:
            print(f"❌ Failed to update Airtable for {website}: {e}")

    print(f"\n🏁 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
