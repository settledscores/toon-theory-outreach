from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import os
from pyairtable import Table
from dotenv import load_dotenv

load_dotenv()

# Airtable setup using pyairtable
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
airtable = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# Prioritized list: higher priority comes first
SERVICE_PATHS = [
    "/services", "/solutions", "/what-we-do",  # High priority
    "/offerings", "/capabilities", "/expertise"  # Lower priority
]

# Extract visible body text from HTML
def extract_visible_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "header", "form", "svg", "img", "a"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

# Try all service paths and return the longest valid content
def scrape_service_content(website):
    if not website.startswith("http"):
        website = "https://" + website

    parsed = urlparse(website)
    base = f"{parsed.scheme}://{parsed.netloc}"

    best_text = ""
    best_url = None

    for path in SERVICE_PATHS:
        url = urljoin(base, path)
        try:
            res = requests.get(url, timeout=10)
            if res.ok:
                text = extract_visible_text(res.text)
                if len(text) > 300:
                    print(f"✅ Valid content at {url} ({len(text)} chars)")
                    if len(text) > len(best_text):
                        best_text = text
                        best_url = url
        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")

    if best_text:
        print(f"🏆 Selected: {best_url}")
    else:
        print(f"❌ No valid service content found for {website}")

    return best_text if best_text else None

# Airtable loop
def main():
    records = airtable.all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website", "").strip()

        if not website or fields.get("services"):
            continue

        print(f"\n🔍 Scraping services for: {website}")
        content = scrape_service_content(website)
        if content:
            airtable.update(record["id"], {"services": content})
            print(f"✅ Services field updated for {website}")
            updated_count += 1
        else:
            print(f"⛔ Skipped: No content found for {website}")

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
