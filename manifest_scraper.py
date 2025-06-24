import requests
import os

SCRAPER_API_KEY = os.getenv("CLUTCH_SCRAPER_API_KEY")
BASE_URL = "https://themanifest.com/business-consulting/firms?page=0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_with_scraperapi(url):
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    try:
        res = requests.get(proxy_url, headers=HEADERS)
        if res.status_code == 200:
            return res.text
        else:
            print(f"❌ Failed to fetch: {url} (status {res.status_code})")
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
    return None

def main():
    print("🔍 Fetching raw HTML for inspection...")
    html = fetch_with_scraperapi(BASE_URL)
    if html:
        print(html[:5000])  # print the first 5000 characters
    else:
        print("❌ Failed to retrieve HTML.")

if __name__ == "__main__":
    main()
