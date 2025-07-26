import os
import json
import re
import requests
import urllib3
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

# === Config ===
INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/emails.txt"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ToonTheoryBot/1.0; +https://toontheory.com)"}
RELEVANT_KEYWORDS = ["about", "contact", "team", "our-story", "story", "who-we-are", "leadership", "staff"]
IRRELEVANT_KEYWORDS = ["blog", "news", "faq", "privacy", "terms", "careers", "jobs", "cookies"]

# === Setup ===
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def is_relevant_link(href):
    href_lower = href.lower()
    if any(x in href_lower for x in IRRELEVANT_KEYWORDS):
        return False
    if any(x in href_lower for x in RELEVANT_KEYWORDS):
        return True
    return False

def fetch_with_retries(url):
    for scheme in ["https", "http"]:
        try:
            parsed = urlparse(url)
            test_url = parsed._replace(scheme=scheme).geturl()
            res = requests.get(test_url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                return res.text
        except Exception as e:
            print(f"  ⚠️ Failed {scheme.upper()} fetch: {e}")
    return ""

def crawl_all_pages(start_url):
    visited = set()
    to_visit = [start_url]
    domain = urlparse(start_url).netloc
    full_text = ""
    page_count = 0

    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue

        print(f"  🕸️ Visiting: {url}")
        html = fetch_with_retries(url)
        if not html:
            print("  ⚠️ No HTML content, skipping.")
            continue

        visited.add(url)
        soup = BeautifulSoup(html, "html.parser")
        page_text = soup.get_text(separator=' ', strip=True)
        full_text += page_text + " "
        page_count += 1
        print(f"  📄 +{len(page_text)} chars from {url}")

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])
            parsed = urlparse(href)
            if parsed.netloc == domain and href not in visited and href not in to_visit:
                if is_relevant_link(href):
                    to_visit.append(href)
                    print(f"    ➕ Queueing: {href}")
                else:
                    print(f"    🚫 Skipping irrelevant: {href}")

    print(f"  🔚 Finished crawling {page_count} pages from {start_url}")
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
    total_skipped = 0

    print("📥 Starting email scraping from leads...\n")

    for i, record in enumerate(read_multiline_ndjson(INPUT_PATH), 1):
        first = record.get("first name", "").strip().lower()
        last = record.get("last name", "").strip().lower()
        domain = extract_domain(record.get("website url", ""))
        web_copy = record.get("web copy", "").strip()
        website_url = record.get("website url", "").strip()
        existing_email = record.get("email", "").strip()

        if existing_email:
            print(f"⏭️ Skipping #{i} — already has email: {existing_email}")
            total_skipped += 1
            continue

        missing_fields = []
        if not first: missing_fields.append("first name")
        if not last: missing_fields.append("last name")
        if not domain: missing_fields.append("domain")
        if not web_copy: missing_fields.append("web copy")

        if missing_fields:
            print(f"⏭️ Skipping #{i} — missing {', '.join(missing_fields)}")
            total_skipped += 1
            continue

        total_checked += 1
        norm_url = normalize_url(website_url)
        print(f"\n🌐 Crawling #{i}: {norm_url} for {first} {last} [{domain}]")

        full_text = crawl_all_pages(norm_url)
        found_emails = extract_emails(full_text)

        match_found = False
        for email in found_emails:
            if is_match(email, domain, first, last):
                matches.add(email.lower())
                total_matched += 1
                print(f"  ✅ Match: {email}")
                match_found = True
                break

        if not match_found:
            print("  ❌ No match found")

    print("\n📊 Scrape Summary")
    print(f"✔️ Leads checked: {total_checked}")
    print(f"⏭️ Leads skipped: {total_skipped}")
    print(f"📬 Emails matched: {total_matched}")

    if matches:
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(matches)) + "\n")
        print(f"\n✅ Saved {len(matches)} emails to {OUTPUT_PATH}")
    else:
        print("⚠️ No valid emails found.")

if __name__ == "__main__":
    main()
