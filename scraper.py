import os
import requests
from bs4 import BeautifulSoup
from airtable import Airtable
from dotenv import load_dotenv
from urllib.parse import urljoin, urlparse

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

COMMON_SERVICE_PATHS = [
    "",  # homepage
    "services",
    "what-we-do",
    "solutions",
    "offerings",
    "capabilities",
    "how-it-works",
]

def fetch_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form", "aside"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())

def try_scrape_url(base_url):
    for path in COMMON_SERVICE_PATHS:
        full_url = urljoin(base_url + "/", path)
        try:
            response = requests.get(full_url, timeout=10)
            if response.status_code == 200:
                content = fetch_visible_text(response.text)
                if len(content.split()) > 50:
                    return content
        except Exception as e:
            continue
    return ""

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
            continue  # Skip if no website or already scraped

        norm_url = normalize_url(website)
        print(f"🌐 Scraping: {norm_url}")

        try:
            text = try_scrape_url(norm_url)
            if text:
                airtable.update(record["id"], {"web copy": text})
                print(f"✅ Updated: {website}")
                updated_count += 1
            else:
                print(f"⚠️ No usable content for {website}")
        except Exception as e:
            print(f"❌ Failed to scrape {website}: {e}")

    print(f"\n🔚 Finished scraping. {updated_count} records updated.")

if __name__ == "__main__":
    main()
