import os
import requests
import re
from airtable import Airtable
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load .env secrets
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")
SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Limit to 5 entries for now
MAX_RECORDS = 5

def looks_like_name(text):
    words = text.strip().split()
    if len(words) < 2 or len(words) > 4:
        return False
    if text.lower().startswith(("your", "data", "terms", "privacy", "provides")):
        return False
    if any(word.islower() for word in words):
        return False
    return True

def extract_name_from_snippet(snippet):
    # Try to find name + title format: "Jane Doe, Founder" or "John Smith is the Managing Partner"
    match = re.search(r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+)[,\s]+(Founder|Owner|Partner|Principal|Director|Managing.*)", snippet)
    if match:
        return match.group(1), match.group(0)
    # Fallback: find any likely name
    match = re.search(r"([A-Z][a-z]+(?:\s[A-Z]\.)?\s[A-Z][a-z]+)", snippet)
    if match and looks_like_name(match.group(1)):
        return match.group(1), snippet
    return "", snippet

def search_duckduckgo(query):
    encoded_query = quote_plus(query)
    ddg_url = f"https://duckduckgo.com/html/?q={encoded_query}"
    proxy_url = f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={ddg_url}"

    try:
        res = requests.get(proxy_url, timeout=20)
        if res.status_code != 200:
            print(f"❌ DDG request failed: {res.status_code}")
            return "", "", ddg_url

        snippets = re.findall(r'<a[^>]+class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>.*?<a href="([^"]+)"', res.text, re.DOTALL)
        for html_snippet, url in snippets[:5]:
            snippet_text = re.sub(r"<.*?>", "", html_snippet)
            name, preview = extract_name_from_snippet(snippet_text)
            if name:
                return name, preview, url
    except Exception as e:
        print(f"⚠️ Error scraping DDG: {e}")
    return "", "", ddg_url

def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        if updated >= MAX_RECORDS:
            break

        fields = record.get("fields", {})
        biz_name = fields.get("business name", "").strip()
        website = fields.get("website url", "").strip()

        if not biz_name and not website:
            continue

        search_query = f"{biz_name} founder OR owner OR managing partner"
        print(f"🔍 Searching DDG for: {search_query}")

        name, snippet, found_url = search_duckduckgo(search_query)
        if not name and website:
            domain = website.replace("https://", "").replace("http://", "").split("/")[0]
            search_query = f"site:{domain} founder OR owner OR principal"
            print(f"↪️ Retrying with domain: {search_query}")
            name, snippet, found_url = search_duckduckgo(search_query)

        if name:
            airtable.update(record["id"], {
                "DDG Name": name,
                "DDG Snippet": snippet,
                "DDG URL": found_url,
                "Found By": "duckduckgo"
            })
            print(f"✅ Found: {name}")
            updated += 1
        else:
            print(f"❌ No name found for {biz_name or website}")

    print(f"\n🏁 Finished. {updated} record(s) updated.")

if __name__ == "__main__":
    main()
