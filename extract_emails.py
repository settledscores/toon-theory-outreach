import os
import json
import re
import requests
import urllib3
from urllib.parse import urlparse as original_urlparse, urljoin
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

# === Warnings & Patching ===
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def safe_urlparse(url):
    try:
        parsed = original_urlparse(url)
        if "[" in parsed.netloc or "]" in parsed.netloc:
            raise ValueError("Invalid bracketed address")
        return parsed
    except Exception as e:
        print(f"⛔ Skipping malformed URL: {url} — {e}")
        return None

urlparse = safe_urlparse

# === Paths ===
INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/emails.txt"

# === Setup ===
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ToonTheoryBot/1.0; +https://toontheory.com)"
}
RELEVANT_KEYWORDS = {
    "about", "team", "contact", "leadership", "our-story", "who-we-are",
    "people", "company", "founder", "bio", "management", "executives", "us"
}
IRRELEVANT_KEYWORDS = {
    "blog", "faq", "faqs", "terms", "privacy", "policy", "careers", "jobs",
    "news", "events", "press", "sitemap", "cookies"
}
GENERIC_EMAILS = {"info@", "support@", "help@", "hello@", "admin@"}

# === Helpers ===
def extract_domain(url):
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "").lower() if parsed else ""
    except:
        return ""

def normalize_url(url):
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        url = f"https://{url}"
    parsed = urlparse(url)
    return parsed.geturl() if parsed else ""

def fetch_html(url):
    for scheme in ["https", "http"]:
        try:
            parsed = urlparse(url)
            if not parsed: continue
            test_url = parsed._replace(scheme=scheme).geturl()
            res = requests.get(test_url, headers=HEADERS, timeout=10, verify=False)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                return res.text
        except:
            continue
    return ""

def extract_emails(text):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

def is_match(email, domain, first, last):
    if not email.endswith("@" + domain):
        return False
    local = email.split("@")[0].lower()
    if any(email.startswith(prefix) for prefix in GENERIC_EMAILS):
        return False
    return first in local or last in local

def collect_relevant_links(index_html, base_url, domain):
    soup = BeautifulSoup(index_html, "html.parser")
    eligible = []
    skipped = 0

    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link["href"])
        parsed = urlparse(href)
        if not parsed: continue
        path = parsed.path.lower()

        if parsed.netloc and parsed.netloc != domain:
            continue

        if any(bad in path for bad in IRRELEVANT_KEYWORDS):
            skipped += 1
            continue
        if any(good in path for good in RELEVANT_KEYWORDS):
            eligible.append(href)

    return list(dict.fromkeys(eligible))[:20], skipped

def read_multiline_ndjson(path):
    with open(path, "r", encoding="utf-8") as f:
        buffer = ""
        for line in f:
            if not line.strip():
                continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    yield json.loads(buffer)
                except:
                    pass
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
        website_url = record.get("website url", "").strip()
        web_copy = record.get("web copy", "").strip()
        domain = extract_domain(website_url)
        email = record.get("email", "").strip()

        missing = []
        if not first: missing.append("first name")
        if not last: missing.append("last name")
        if not domain: missing.append("domain")
        if not web_copy: missing.append("web copy")
        if email: missing.append("email already present")

        if missing:
            print(f"⏭️ Skipping #{i} — {', '.join(missing)}")
            total_skipped += 1
            continue

        total_checked += 1
        norm_url = normalize_url(website_url)
        print(f"\n🌐 Checking #{i}: {norm_url} for {first} {last} [{domain}]")

        index_html = fetch_html(norm_url)
        if not index_html:
            print("  ⚠️ Couldn't load index page.")
            continue

        index_emails = extract_emails(index_html)
        for email in index_emails:
            if is_match(email, domain, first, last):
                print(f"  ✅ Found matching email on index: {email}")
                matches.add(email.lower())
                total_matched += 1
                break
        else:
            relevant_links, skipped = collect_relevant_links(index_html, norm_url, domain)
            if skipped > 0:
                print(f"  🔍 Skipped all irrelevant URLs for {domain}")
            found = False
            for link in relevant_links:
                html = fetch_html(link)
                if not html:
                    continue
                emails = extract_emails(html)
                for email in emails:
                    if is_match(email, domain, first, last):
                        print(f"  ✅ Found matching email on {link}: {email}")
                        matches.add(email.lower())
                        total_matched += 1
                        found = True
                        break
                if found:
                    break
            if not found:
                print("  ❌ No matching email found")

    # === Final Output ===
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
