import os
import re
import json
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse as original_urlparse

# === Settings ===
SCRAPED_LEADS_PATH = "leads/scraped_leads.ndjson"
MAX_PAGES = 10
CHAR_COUNT_THRESHOLD = 2000
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ToonTheoryBot/1.0; +https://toontheory.com)"
}

# === Init ===
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Safe urlparse wrapper ===
def safe_urlparse(url):
    try:
        parsed = original_urlparse(url)
        if "[" in parsed.netloc or "]" in parsed.netloc:
            raise ValueError("Invalid bracketed netloc")
        return parsed
    except Exception as e:
        print(f"⛔ Skipping malformed URL: {url} — {e}")
        return None

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
        url = f"https://{url}"
    parsed = safe_urlparse(url)
    return parsed.geturl() if parsed else None

def fetch_with_retries(url):
    for scheme in ["https", "http"]:
        parsed = safe_urlparse(url)
        if not parsed:
            return None
        test_url = parsed._replace(scheme=scheme).geturl()
        try:
            res = requests.get(test_url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                return res
        except Exception as e:
            print(f"⚠️ {scheme.upper()} fetch failed: {e}")
    return None

def crawl_site(base_url, max_pages=MAX_PAGES):
    visited = set()
    to_visit = [base_url]
    parsed_base = safe_urlparse(base_url)
    if not parsed_base:
        return ""
    domain = parsed_base.netloc
    all_text = ""

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        res = fetch_with_retries(url)
        if not res:
            print(f"⚠️ Skipped (fetch failed): {url}")
            continue

        visited.add(url)
        print(f"🔍 Crawled: {url}")

        soup = BeautifulSoup(res.text, "html.parser")
        visible = extract_visible_text(res.text)
        all_text += clean_text(visible) + " "

        for a in soup.find_all("a", href=True):
            raw_href = a["href"]
            try:
                joined_href = urljoin(url, raw_href)
                parsed = safe_urlparse(joined_href)
                if not parsed:
                    continue
                href = parsed.geturl()
                if parsed.netloc != domain or href in visited or href in to_visit:
                    continue
                to_visit.append(href)
            except Exception as e:
                print(f"⛔ Skipping bad link ({raw_href}): {e}")
                continue

    return all_text.strip()

def read_ndjson_nested(path):
    buffer = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                if buffer.strip():
                    try:
                        yield json.loads(buffer)
                    except Exception as e:
                        print(f"❌ Bad record skipped: {e}")
                    buffer = ""
            else:
                buffer += line
        if buffer.strip():
            try:
                yield json.loads(buffer)
            except Exception as e:
                print(f"❌ Final record skipped: {e}")

def write_ndjson_nested(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, indent=2, ensure_ascii=False)
            f.write("\n\n")

def main():
    if not os.path.exists(SCRAPED_LEADS_PATH):
        print(f"❌ Missing: {SCRAPED_LEADS_PATH}")
        return

    updated = []
    changed = False

    for i, lead in enumerate(read_ndjson_nested(SCRAPED_LEADS_PATH), 1):
        url = lead.get("website url", "").strip()

        if "web copy" not in lead:
            print(f"⏭️ #{i}: No 'web copy' field — skipping")
            updated.append(lead)
            continue

        if not url:
            print(f"⏭️ #{i}: No website URL")
            updated.append(lead)
            continue

        if lead["web copy"].strip():
            print(f"⏭️ #{i}: Already has web copy")
            updated.append(lead)
            continue

        norm_url = normalize_url(url)
        if not norm_url:
            print(f"⛔ #{i}: Invalid URL — skipping")
            updated.append(lead)
            continue

        print(f"\n🌐 #{i}: {norm_url}")
        content = crawl_site(norm_url)
        char_count = len(content)

        if char_count < CHAR_COUNT_THRESHOLD:
            print(f"⚠️ Not enough characters ({char_count}) — ineligible")
            lead["web copy"] = ""
        else:
            print(f"✅ Eligible — {char_count} characters scraped")
            lead["web copy"] = str(char_count)
            changed = True

        updated.append(lead)

    if changed:
        write_ndjson_nested(SCRAPED_LEADS_PATH, updated)
        print(f"\n📝 Updated file: {SCRAPED_LEADS_PATH}")
    else:
        print("\n⚠️ No updates made")

if __name__ == "__main__":
    main()
