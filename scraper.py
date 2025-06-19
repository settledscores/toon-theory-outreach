import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# === Airtable Setup ===
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# === Common Service Paths ===
COMMON_SERVICE_PATHS = [
    "services",
    "our-services",
    "solutions",
    "what-we-do",
    "how-it-works",
    "capabilities",
    "offerings",
    "products",
    "features",
    "platform",
    ""  # fallback to homepage
]

# === Utility to Extract Visible Text ===
def fetch_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "input"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())  # normalize spacing

# === Try Scraping Best Page ===
def try_scrape_url(base_url):
    best_text = ""
    most_keywords = 0

    for path in COMMON_SERVICE_PATHS:
        full_url = urljoin(base_url + "/", path)
        try:
            response = requests.get(full_url, timeout=10)
            if response.status_code == 200:
                content = fetch_visible_text(response.text)
                keyword_hits = sum(content.lower().count(k) for k in [
                    "services", "solutions", "we help", "we provide", "what we do", "offerings", "capabilities"
                ])
                if keyword_hits > most_keywords and len(content.split()) > 50:
                    best_text = content
                    most_keywords = keyword_hits
        except Exception:
            continue

    return best_text

# === Main Sync Logic ===
def main():
    print("🔎 Starting services scraper...")
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website", "").strip()

        if not website or "services" in fields:
            continue

        print(f"🌐 Scraping services for {website}...")
        text = try_scrape_url(website)

        if text:
            airtable.update(record["id"], {"services": text})
            print("✅ Updated services field")
            updated += 1
        else:
            print("⚠️ No usable content found")

    print(f"🏁 Done. Total updated: {updated}")

if __name__ == "__main__":
    main()
