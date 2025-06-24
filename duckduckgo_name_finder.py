import os
import requests
import re
from airtable import Airtable
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load secrets
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

def looks_like_name(text):
    words = text.strip().split()
    return (
        1 < len(words) < 5 and
        not text.lower().startswith(("your", "data", "terms", "privacy", "provides")) and
        all(word.istitle() for word in words)
    )

def extract_name_from_snippet(snippet):
    snippet_clean = re.sub(r"<.*?>", "", snippet)
    match = re.search(r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+)[,\s]+(Founder|Owner|Partner|Principal|Director|Managing.*)", snippet_clean)
    if match:
        return match.group(1), snippet_clean
    fallback = re.search(r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+)", snippet_clean)
    if fallback and looks_like_name(fallback.group(1)):
        return fallback.group(1), snippet_clean
    return "", snippet_clean

def search_duckduckgo(query):
    encoded_query = quote_plus(query)
    ddg_url = f"https://duckduckgo.com/html/?q={encoded_query}"
    proxy_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={ddg_url}"

    try:
        res = requests.get(proxy_url, timeout=20)
        if res.status_code != 200:
            print(f"❌ DDG request failed: {res.status_code}")
            return "", "", ddg_url

        results = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>.*?<a href="([^"]+)"', res.text, re.DOTALL)
        for html_snippet, url in results[:5]:
            name, preview = extract_name_from_snippet(html_snippet)
            if name:
                return name, preview, url
    except Exception as e:
        print(f"⚠️ Error scraping DDG: {e}")
    return "", "", ddg_url

def main():
    print("🔄 Starting DuckDuckGo name extraction...")

    records = airtable.get_all(sort=["business name"])[:5]
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        biz_name = fields.get("business name", "").strip()
        website = fields.get("website url", "").strip()

        if not biz_name and not website:
            continue

        search_query = f"{biz_name} founder OR owner OR managing partner"
        print(f"\n🔍 Searching DDG for: {search_query}")

        name, snippet, found_url = search_duckduckgo(search_query)

        if not name and website:
            domain = website.replace("https://", "").replace("http://", "").split("/")[0]
            search_query = f"site:{domain} founder OR owner OR principal"
            print(f"↪️ Retrying with domain: {search_query}")
            name, snippet, found_url = search_duckduckgo(search_query)

        if name:
            try:
                airtable.update(record["id"], {
                    "DDG Name": name,
                    "DDG Snippet": snippet,
                    "DDG URL": found_url,
                    "Found By": "duckduckgo"
                })
                print(f"✅ Found and updated: {name}")
                updated += 1
            except Exception as e:
                print(f"❌ Airtable update failed: {e}")
        else:
            print("❌ No name found.")

    print(f"\n🏁 Done. {updated} record(s) updated.")

if __name__ == "__main__":
    main()
