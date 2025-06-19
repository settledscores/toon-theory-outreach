import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1; +https://example.com/bot)"
}

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "svg", "img", "noscript", "aside"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

def crawl_site(base_url, max_pages=15):
    visited = set()
    to_visit = [base_url]
    domain = urlparse(base_url).netloc
    full_text = ""

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
                full_text += extract_visible_text(res.text) + " "

                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    joined = urljoin(url, href)
                    if domain in urlparse(joined).netloc and joined not in visited:
                        to_visit.append(joined)
        except Exception as e:
            print(f"⚠️ Failed to fetch {url}: {e}")
            continue

    return " ".join(full_text.split())

def normalize_url(url):
    if not url.startswith("http"):
        return "https://" + url.strip("/")
    return url.strip("/")

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

        if len(text.split()) > 50:
            airtable.update(record["id"], {"web copy": text})
            print(f"✅ Updated {website}")
            updated_count += 1
        else:
            print(f"⚠️ Not enough content found for {website}")

    print(f"\n🏁 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
