import os
import re
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SCRAPED_LEADS_PATH = "leads/scraped_leads.ndjson"
MAX_PAGES = 10
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
    if not url.startswith("http"):
        return f"https://{url}"
    return url

def fetch_with_retries(url):
    """Attempt HTTPS first, then HTTP fallback, with basic retry handling."""
    schemes = ["https", "http"]
    parsed = urlparse(url)
    for scheme in schemes:
        test_url = parsed._replace(scheme=scheme).geturl()
        try:
            res = requests.get(test_url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                return res
        except Exception as e:
            print(f"⚠️ Failed fetch via {scheme.upper()}: {e}")
    return None

def crawl_site(base_url, max_pages=MAX_PAGES):
    visited = set()
    to_visit = [base_url]
    domain = urlparse(base_url).netloc
    all_text = ""

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        res = fetch_with_retries(url)
        if not res:
            continue

        visited.add(url)
        soup = BeautifulSoup(res.text, "html.parser")
        visible_text = extract_visible_text(res.text)
        all_text += visible_text + " "

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            parsed_href = urlparse(href)
            if parsed_href.netloc == domain and href not in visited and href not in to_visit:
                to_visit.append(href)

    return clean_text(all_text)

def read_ndjson_nested(path):
    buffer = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                if buffer.strip():
                    try:
                        yield json.loads(buffer)
                    except Exception as e:
                        print(f"❌ Skipping malformed record: {e}")
                    buffer = ""
            else:
                buffer += line
        if buffer.strip():
            try:
                yield json.loads(buffer)
            except Exception as e:
                print(f"❌ Skipping trailing malformed record: {e}")

def write_ndjson_nested(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, indent=2, ensure_ascii=False)
            f.write("\n\n")

def main():
    if not os.path.exists(SCRAPED_LEADS_PATH):
        print(f"❌ Missing file: {SCRAPED_LEADS_PATH}")
        return

    updated = []
    changed = False

    for i, lead in enumerate(read_ndjson_nested(SCRAPED_LEADS_PATH), 1):
        website = lead.get("website url", "").strip()
        web_copy = lead.get("web copy", "").strip()

        if not website:
            print(f"⏭️ Skipping record #{i} — no website")
            updated.append(lead)
            continue

        if web_copy:
            print(f"⏭️ Skipping record #{i} — already has web copy")
            updated.append(lead)
            continue

        norm_url = normalize_url(website)
        print(f"🌐 Crawling #{i}: {norm_url}")

        content = crawl_site(norm_url)
        word_count = len(content.split())

        if word_count < MIN_WORDS_THRESHOLD:
            print("⚠️ Skipping — not enough content.")
            lead["web copy"] = ""
            updated.append(lead)
            continue

        trimmed = content[:MAX_TEXT_LENGTH]
        char_count = len(trimmed)
        lead["web copy"] = str(char_count)
        updated.append(lead)
        changed = True
        print(f"✅ Scraped {urlparse(norm_url).netloc} ({char_count} chars from {len(content.split())} words)")

    if changed:
        write_ndjson_nested(SCRAPED_LEADS_PATH, updated)
        print(f"\n📝 Updated web copy in {SCRAPED_LEADS_PATH}")
    else:
        print("⚠️ No new web copy to update.")

if __name__ == "__main__":
    main()
