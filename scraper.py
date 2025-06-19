from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import os
from pyairtable import Table
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
airtable = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# Prioritized service-related paths
SERVICE_PATHS = [
    "/services", "/solutions", "/what-we-do",  # High priority
    "/offerings", "/capabilities", "/expertise"  # Lower priority
]

# Extracts visible body text from an HTML document
def extract_visible_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "header", "form", "svg", "img", "a"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

# Tries all service-like URLs, returns best match based on length
def scrape_service_content(website):
    if not website.startswith("http"):
        website = "https://" + website

    parsed = urlparse(website)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    best_text = ""
    best_url = None

    for path in SERVICE_PATHS:
        full_url = urljoin(base_url, path)
        try:
            response = requests.get(full_url, timeout=10)
            if response.ok:
                text = extract_visible_text(response.text)
                if len(text) > 300:
                    print(f"✅ Found content at {full_url} ({len(text)} chars)")
                    if len(text) > len(best_text):
                        best_text = text
                        best_url = full_url
        except Exception as e:
            print(f"⚠️ Failed to fetch {full_url}: {e}")

    if best_text:
        print(f"🏆 Best match: {best_url}")
        return best_text
    else:
        print(f"❌ No service content found for {website}")
        return None

# Main Airtable loop
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
            print(f"✅ Updated: {website}")
            updated_count += 1
        else:
            print(f"⛔ No valid content for {website}")

    print(f"\n🎯 Done. Updated services for {updated_count} records.")

if __name__ == "__main__":
    main()
