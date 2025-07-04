import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime

SCRAPED_LEADS_PATH = "leads/scraped_leads.ndjson"

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

def read_ndjson_nested(path):
    records = []
    buffer = []
    depth = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            depth += line.count("{") - line.count("}")
            buffer.append(line)

            if depth == 0 and buffer:
                try:
                    raw = "\n".join(buffer)
                    records.append(json.loads(raw))
                except json.JSONDecodeError as e:
                    print(f"❌ Skipping malformed record: {e}")
                buffer = []
    return records

def write_ndjson_nested(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, indent=2, ensure_ascii=False)
            f.write("\n\n")

def main():
    if not os.path.exists(SCRAPED_LEADS_PATH):
        print(f"❌ Missing file: {SCRAPED_LEADS_PATH}")
        return

    try:
        leads = read_ndjson_nested(SCRAPED_LEADS_PATH)
    except Exception as e:
        print(f"❌ Failed to load leads: {e}")
        return

    updated = []
    changed = False

    for idx, lead in enumerate(leads):
        website = lead.get("website url", "").strip()
        web_copy = lead.get("web copy", "").strip()

        if not website:
            print(f"⚠️ Skipping record #{idx + 1} — no website")
            updated.append(lead)
            continue

        if web_copy:
            print(f"⏭️ Skipping record #{idx + 1} — already has web copy")
            updated.append(lead)
            continue

        norm_url = normalize_url(website)
        print(f"🌐 Crawling record #{idx + 1}: {norm_url}")

        content = crawl_site(norm_url)
        if len(content.split()) < MIN_WORDS_THRESHOLD:
            print("⚠️ Not enough content, skipping.")
            updated.append(lead)
            continue

        trimmed = content[:MAX_TEXT_LENGTH]
        lead["web copy"] = trimmed
        updated.append(lead)
        changed = True
        print(f"✅ Scraped and saved for {urlparse(norm_url).netloc}")

    if changed:
        try:
            write_ndjson_nested(SCRAPED_LEADS_PATH, updated)
            print(f"\n📝 Updated web copy in {SCRAPED_LEADS_PATH}")
        except Exception as e:
            print(f"❌ Failed to write updated leads: {e}")
    else:
        print("⚠️ No new web copy to update.")

if __name__ == "__main__":
    main()
