import os
import re
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# === Settings ===
SCRAPED_LEADS_PATH = "leads/scraped_leads.ndjson"
MAX_PAGES = 10
CHAR_COUNT_THRESHOLD = 2000
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ToonTheoryBot/1.0; +https://toontheory.com)"
}

# === Init ===
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    """Remove non-ASCII and normalize whitespace."""
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return " ".join(text.split())

def extract_visible_text(html):
    """Extract all visible, non-boilerplate text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "form", "svg", "img", "noscript", "aside"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

def normalize_url(url):
    """Ensure it starts with http/https and no trailing slash."""
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        return f"https://{url}"
    return url

def fetch_with_retries(url):
    """Try both HTTPS and HTTP with fallback."""
    for scheme in ["https", "http"]:
        parsed = urlparse(url)
        test_url = parsed._replace(scheme=scheme).geturl()
        try:
            res = requests.get(test_url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                return res
        except Exception as e:
            print(f"⚠️ Fetch error via {scheme.upper()}: {e}")
    return None

def crawl_site(base_url, max_pages=MAX_PAGES):
    visited = set()
    to_visit = [base_url]
    domain = urlparse(base_url).netloc
    combined_text = ""

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        res = fetch_with_retries(url)
        if not res:
            print(f"⚠️ Skipped page (fetch failed): {url}")
            continue

        visited.add(url)
        print(f"🔍 Crawling: {url}")

        soup = BeautifulSoup(res.text, "html.parser")
        visible_text = extract_visible_text(res.text)
        cleaned = clean_text(visible_text)
        combined_text += cleaned + " "

        # Collect internal links to visit
        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            parsed = urlparse(href)
            if parsed.netloc == domain and href not in visited and href not in to_visit:
                to_visit.append(href)

    return combined_text.strip()

def read_ndjson_nested(path):
    buffer = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                if buffer.strip():
                    try:
                        yield json.loads(buffer)
                    except Exception as e:
                        print(f"❌ Malformed record skipped: {e}")
                    buffer = ""
            else:
                buffer += line
        if buffer.strip():
            try:
                yield json.loads(buffer)
            except Exception as e:
                print(f"❌ Trailing record skipped: {e}")

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
        existing_copy = lead.get("web copy", "").strip()

        if not website:
            print(f"⏭️ Skipping #{i}: No website URL")
            updated.append(lead)
            continue

        if existing_copy:
            print(f"⏭️ Skipping #{i}: Already has web copy")
            updated.append(lead)
            continue

        norm_url = normalize_url(website)
        print(f"\n🌐 Processing #{i}: {norm_url}")

        content = crawl_site(norm_url)
        char_count = len(content)

        if char_count < CHAR_COUNT_THRESHOLD:
            print(f"⚠️ Not enough content ({char_count} chars) — skipping.")
            lead["web copy"] = ""
        else:
            print(f"✅ Eligible — {char_count} characters scraped.")
            lead["web copy"] = str(char_count)
            changed = True

        updated.append(lead)

    if changed:
        write_ndjson_nested(SCRAPED_LEADS_PATH, updated)
        print(f"\n📝 Saved updated leads to: {SCRAPED_LEADS_PATH}")
    else:
        print("\n⚠️ No updates made — all leads already processed or skipped.")

if __name__ == "__main__":
    main()
