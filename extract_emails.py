import os
import json
import re
import requests
import urllib3
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Paths ===
INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/emails.txt"

# === Setup ===
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ToonTheoryBot/1.0; +https://toontheory.com)"}

# === Helpers ===
def extract_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "").lower()
    except:
        return ""

def extract_emails(text):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

def is_match(email, domain, first, last):
    if not email.endswith("@" + domain):
        return False
    local = email.split("@")[0].lower()
    return first.lower() in local or last.lower() in local

def normalize_url(url):
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        return f"https://{url}"
    return url

def fetch_with_retries(url):
    for scheme in ["https", "http"]:
        try:
            parsed = urlparse(url)
            test_url = parsed._replace(scheme=scheme).geturl()
            res = requests.get(test_url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                return res.text
        except Exception as e:
            print(f"⚠️ Failed fetch {scheme.upper()} {url}: {e}")
    return ""

def crawl_all_pages(start_url):
    visited = set()
    to_visit = [start_url]
    domain = urlparse(start_url).netloc
    full_text = ""

    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue

        html = fetch_with_retries(url)
        if not html:
            continue

        visited.add(url)
        soup = BeautifulSoup(html, "html.parser")
        full_text += soup.get_text(separator=' ', strip=True) + " "

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            parsed = urlparse(href)
            if parsed.netloc == domain and href not in visited and href not in to_visit:
                to_visit.append(href)

    return full_text

def read_multiline_ndjson(path):
    with open(path, "r", encoding="utf-8") as f:
        buffer = ""
        for line in f:
            if line.strip() == "":
                continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    yield json.loads(buffer)
                except Exception as e:
                    print(f"❌ Skipping invalid JSON block: {e}")
                buffer = ""

# === Main ===
def main():
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Input file not found: {INPUT_PATH}")
        return

    matches = set()
    total_checked = 0
    total_matched = 0

    print("📥 Starting email scraping from leads...")

    for i, record in enumerate(read_multiline_ndjson(INPUT_PATH), 1):
        first = record.get("first name", "").strip().lower()
        last = record.get("last name", "").strip().lower()
        domain = extract_domain(record.get("website url", ""))
        web_copy = record.get("web copy", "").strip()
        website_url = record.get("website url", "").strip()

        if not (first and last and domain and web_copy):
            print(f"⏭️ Skipping #{i} — missing required fields.")
            continue

        total_checked += 1
        norm_url = normalize_url(website_url)
        print(f"🌐 Crawling #{i}: {norm_url}")

        full_text = crawl_all_pages(norm_url)
        found_emails = extract_emails(full_text)

        match_found = False
        for email in found_emails:
            if is_match(email, domain, first, last):
                matches.add(email.lower())
                total_matched += 1
                print(f"✅ Match: {email} for {first} {last} at {domain}")
                match_found = True
                break

        if not match_found:
            print(f"❌ No match found for #{i}")

    if matches:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(matches)) + "\n")
        print(f"\n✅ Extracted {len(matches)} emails from {total_checked} leads.")
        print(f"📄 Saved to {OUTPUT_PATH}")
    else:
        print("⚠️ No valid emails found.")

if __name__ == "__main__":
    main()
