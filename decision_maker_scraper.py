import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from airtable import Airtable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
SCRAPER_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")

airtable = Airtable(AIRTABLE_BASE_ID, SCRAPER_TABLE_NAME, AIRTABLE_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1; +https://example.com/bot)"
}

MAX_PAGES = 15
REQUEST_TIMEOUT = 10

# Patterns to match names, titles, emails, LinkedIn
EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
LINKEDIN_REGEX = r"https?://(www\.)?linkedin\.com/in/[^\s\"'>]+"
TITLE_KEYWORDS = ["CEO", "Founder", "Managing Partner", "President", "Principal", "Owner", "Director"]

def normalize_url(url):
    url = url.strip().rstrip("/")
    return url if url.startswith("http") else f"https://{url}"

def extract_people_info(html):
    soup = BeautifulSoup(html, "html.parser")
    names_titles = []
    emails = set()
    linkedins = set()

    for tag in soup.find_all(['p', 'div', 'li', 'span', 'a']):
        text = tag.get_text(" ", strip=True)

        # Look for titles
        for title in TITLE_KEYWORDS:
            if title.lower() in text.lower() and len(text.split()) <= 10:
                names_titles.append((text, title))

        # Emails
        found_emails = re.findall(EMAIL_REGEX, text)
        for email in found_emails:
            if not email.lower().endswith((".png", ".jpg", ".jpeg")):
                emails.add(email)

        # LinkedIn
        found_links = re.findall(LINKEDIN_REGEX, text)
        linkedins.update(found_links)

    return names_titles, list(emails), list(linkedins)

def crawl_site(base_url, max_pages=MAX_PAGES):
    visited = set()
    to_visit = [base_url]
    domain = urlparse(base_url).netloc
    people, all_emails, all_linkedins = [], [], []

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        try:
            res = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                visited.add(url)
                print(f"🕷️ Crawling: {url}")
                names, emails, linkedins = extract_people_info(res.text)
                people.extend(names)
                all_emails.extend(emails)
                all_linkedins.extend(linkedins)

                soup = BeautifulSoup(res.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = urljoin(url, link["href"])
                    if urlparse(href).netloc == domain and href not in visited:
                        to_visit.append(href)
        except Exception as e:
            print(f"⚠️ Failed to fetch {url}: {e}")
            continue

    return people, list(set(all_emails)), list(set(all_linkedins))

def guess_email_permutations(name, domain):
    name = name.lower()
    parts = name.split()
    if len(parts) < 2:
        return []
    first, last = parts[0], parts[-1]
    return [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}{last}@{domain}",
        f"{first}_{last}@{domain}"
    ]

def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website") or fields.get("website url")
        if not website:
            continue

        norm_url = normalize_url(website)
        print(f"\n🌐 Crawling: {norm_url}")
        people, emails, linkedins = crawl_site(norm_url)

        if not people:
            print("❌ No decision makers found.")
            continue

        # Choose best match (first with a real title)
        best_person = people[0]
        name, title = best_person if isinstance(best_person, tuple) else (best_person, "Unknown")
        email = emails[0] if emails else ""
        email_source = "website" if email else "guessed"

        # Guess email permutations
        domain = urlparse(norm_url).netloc.replace("www.", "")
        permutations = guess_email_permutations(name, domain) if not email else []

        update_data = {
            "Decision Maker Name": name,
            "Decision Maker Title": title,
            "Decision Maker Email": email,
            "LinkedIn URL": linkedins[0] if linkedins else "",
            "Email Source": email_source,
            "Email Permutations": ", ".join(permutations) if permutations else ""
        }

        try:
            airtable.update(record["id"], update_data)
            print(f"✅ Updated: {name} | {email or 'no email'}")
            updated += 1
        except Exception as e:
            print(f"❌ Failed to update Airtable: {e}")

    print(f"\n🏁 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
