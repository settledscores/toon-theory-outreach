import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

airtable = Airtable(AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME, AIRTABLE_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1; +https://example.com/bot)"
}

BASE_URL = "https://www.bbb.org"
SEARCH_URL = "https://www.bbb.org/search?find_country=USA&find_entity=60005-101&find_id=1_100&find_latlng=30.314613%2C-97.793745&find_loc=Austin%2C%20TX&find_text=Accounting&find_type=Category&page=1&sort=Relevance"

MAX_LEADS = 5
REQUEST_INTERVAL = 3  # seconds

def get_search_results():
    res = requests.get(SEARCH_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, 'html.parser')
    links = soup.select("a.Link__StyledLink-sc-1dh2vhu-0")
    return [urljoin(BASE_URL, link['href']) for link in links if "/profile/" in link['href']][:MAX_LEADS]

def scrape_profile(url):
    try:
        print(f"🔍 Scraping: {url}")
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')

        business_name = soup.select_one("h1[class*=Heading__HeadingStyled]")
        website_url = soup.find("a", string="Visit Website")
        notes = soup.select_one("section p")
        location = soup.select_one("address")
        years = soup.find(text=lambda t: t and "years in business" in t.lower())

        decision_section = soup.find("h2", string=lambda s: s and "Business Management" in s)
        name, title = "", ""
        if decision_section:
            li = decision_section.find_next("li")
            if li:
                parts = list(li.stripped_strings)
                if len(parts) >= 2:
                    name, title = parts[0], parts[1]
                elif len(parts) == 1:
                    name = parts[0]

        domain = website_url['href'].replace("https://", "").replace("http://", "").strip("/") if website_url else ""
        first, last = (name.split(" ")[0], name.split(" ")[-1]) if name else ("", "")
        perms = []
        if first and last and domain:
            perms = [
                f"{first}@{domain}",
                f"{first}.{last}@{domain}",
                f"{first[0]}{last}@{domain}",
                f"{first}{last}@{domain}",
                f"{first}_{last}@{domain}"
            ]

        fields = {
            "website url": website_url['href'] if website_url else "",
            "notes": notes.text.strip() if notes else "",
            "location": location.text.strip() + ", US" if location else "Austin, US",
            "industry": "Accounting",
            "years": years.strip() if years else "",
            "Decision Maker Name": name,
            "Decision Maker Title": title,
            "Email Permutations": "\n".join(perms)
        }

        airtable.insert(fields)
        print(f"✅ Uploaded: {name or '[No Name]'}")

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")


def main():
    profile_links = get_search_results()
    for url in profile_links:
        scrape_profile(url)
        time.sleep(REQUEST_INTERVAL)

if __name__ == "__main__":
    main()
