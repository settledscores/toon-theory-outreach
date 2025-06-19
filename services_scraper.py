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

# Common service page paths to try
SERVICE_PATHS = [
    "services", "solutions", "what-we-do", "offerings", "capabilities", "how-it-works"
]

def extract_visible_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "form", "aside", "svg", "img", "a"]):
        tag.decompose()
    return " ".join(soup.stripped_strings)

def normalize_url(url):
    if not url.startswith("http"):
        return "https://" + url.strip("/")
    return url.strip("/")

def try_scrape_service_page(base_url):
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"

    best_text = ""
    for path in SERVICE_PATHS:
        full_url = urljoin(root + "/", path)
        try:
            res = requests.get(full_url, timeout=10)
            if res.status_code == 200:
                text = extract_visible_text(res.text)
                if len(text.split()) > 50:
                    if len(text) > len(best_text):
                        best_text = text
        except:
            continue
    return best_text

def main():
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website", "")
        current_services = fields.get("services", "")

        if not website or current_services:
            continue

        norm_url = normalize_url(website)
        print(f"🔍 Checking: {norm_url}")
        content = try_scrape_service_page(norm_url)

        if content:
            airtable.update(record["id"], {"services": content})
            print(f"✅ Updated services for: {website}")
            updated_count += 1
        else:
            print(f"⚠️ No usable content for {website}")

    print(f"\n🎯 Finished. {updated_count} records updated.")

if __name__ == "__main__":
    main()
