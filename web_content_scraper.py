import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv
from airtable import Airtable
import re
import time

# Load environment variables
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; WebScraper/1.0; +https://example.com/bot)"
}

MAX_PAGES = 50
TEXT_LIMIT = 25000  # max characters saved in Airtable

def clean_text(text):
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    return " ".join(text.split())

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "form", "header", "svg", "img", "aside"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

def crawl_site(base_url, max_pages=MAX_PAGES):
    domain = urlparse(base_url).netloc
    visited = set()
    to_visit = [base_url]
    full_text = ""

    while to_visit and len(visited) < max_pages and len(full_text) < TEXT_LIMIT:
        url = to_visit.pop(0)
        if url in visited or urlparse(url).netloc != domain:
            continue

        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            if "text/html" not in res.headers.get("Content-Type", ""):
                continue

            visited.add(url)
            print(f"🕷️ Crawling: {url}")
            text = extract_visible_text(res.text)
            full_text += text + "\n"

            soup = BeautifulSoup(res.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = urljoin(url, link["href"])
                if href.startswith(base_url) and href not in visited:
                    to_visit.append(href)

        except Exception as e:
            print(f"⚠️ Error crawling {url}: {e}")
            continue

    return clean_text(full_text[:TEXT_LIMIT])

def normalize_url(url):
    url = url.strip().rstrip("/")
    return url if url.startswith("http") else f"https://{url}"

def main():
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website url", "")
        existing_content = fields.get("content", "")

        if not website or existing_content:
            continue

        norm_url = normalize_url(website)
        print(f"\n🌐 Starting: {norm_url}")
        text = crawl_site(norm_url)

        if len(text.split()) < 50:
            print("⚠️ Skipping — not enough content.")
            continue

        try:
            airtable.update(record["id"], {"content": text})
            print(f"✅ Updated content for: {website}")
            updated_count += 1
        except Exception as e:
            print(f"❌ Failed to update Airtable: {e}")

        time.sleep(1.5)  # mild delay to prevent site blocking

    print(f"\n🏁 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
