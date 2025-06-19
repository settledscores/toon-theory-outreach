import os
import requests
from bs4 import BeautifulSoup
from airtable import Airtable
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()

# Airtable config
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

# Clean and extract visible text
def fetch_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form", "aside"]):
        tag.decompose()
    return " ".join(soup.get_text(separator=" ", strip=True).split())

# Extract a "services" snippet
def extract_services_snippet(text):
    # Find sentences mentioning services, solutions, or offerings
    keywords = ["we offer", "our services", "we provide", "we help", "our team", "solutions include", "capabilities"]
    sentences = text.split(".")
    service_lines = [s.strip() for s in sentences if any(k in s.lower() for k in keywords)]
    snippet = ". ".join(service_lines[:3]).strip()
    return snippet if snippet else text[:300].strip()

# Normalize URL
def normalize_url(url):
    if not url.startswith("http"):
        return "https://" + url.strip("/")
    return url.strip("/")

# Try fetching from common paths
def try_scrape_url(base_url):
    for path in COMMON_SERVICE_PATHS:
        full_url = urljoin(base_url + "/", path)
        try:
            response = requests.get(full_url, timeout=10)
            if response.status_code == 200:
                content = fetch_visible_text(response.text)
                if len(content.split()) > 50:
                    return content
        except Exception:
            continue
    return ""

# Main function
def main():
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website", "")
        web_copy = fields.get("web copy", "")
        services = fields.get("services", "")

        if not website or web_copy:
            continue  # Skip if no website or already scraped

        norm_url = normalize_url(website)
        print(f"🌐 Scraping: {norm_url}")

        try:
            text = try_scrape_url(norm_url)
            if text:
                snippet = extract_services_snippet(text)
                airtable.update(record["id"], {
                    "web copy": text,
                    "services": snippet
                })
                print(f"✅ Updated: {website}")
                updated_count += 1
            else:
                print(f"⚠️ No usable content for {website}")
        except Exception as e:
            print(f"❌ Error scraping {website}: {e}")

    print(f"\n🔚 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
