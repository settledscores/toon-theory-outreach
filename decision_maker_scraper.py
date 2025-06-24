import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("SCRAPER_TABLE_NAME")  # Updated
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Constants
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Bot/0.1; +https://example.com/bot)"}
GENERIC_EMAIL_PREFIXES = {"info", "support", "hello", "contact", "admin", "accounting", "help", "inquiry"}
FREE_EMAIL_PROVIDERS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com"}
TITLE_KEYWORDS = [
    "Managing Partner", "Managing Director", "Founder", "Owner", "Principal", "Partner",
    "President", "Executive Director", "Director", "Firm Principal", "Tax Partner", "Audit Partner",
    "Lead CPA", "Senior CPA", "CPA", "CFE", "EA", "Accountant", "Lead Accountant", "Enrolled Agent"
]
MAX_PAGES = 15

# Email filters
def is_valid_email(email):
    if not email or "@" not in email:
        return False
    prefix, domain = email.split("@", 1)
    return (
        prefix not in GENERIC_EMAIL_PREFIXES and
        domain not in FREE_EMAIL_PROVIDERS and
        not email.endswith((".jpg", ".jpeg", ".png"))
    )

# Name validation
def looks_like_a_name(text):
    if not text or len(text.split()) > 4:
        return False
    if text.strip().lower().startswith(("your", "the", "data", "provides", "25+")):
        return False
    return all(word[0].isupper() for word in text.strip().split()[:2])

# Normalize
def normalize_url(url):
    url = url.strip().rstrip("/")
    return url if url.startswith("http") else f"https://{url}"

# Name cleaner
def clean_name(text):
    text = re.sub(r"\b(CPA|CFE|EA|JD|MBA|PhD|Esq)\b", "", text)
    return re.sub(r"\s+", " ", text).strip(" ,:-")

# Permutation logic
def guess_email_permutations(name, domain):
    parts = name.lower().split()
    if len(parts) < 2:
        return []
    first, last = parts[0], parts[-1]
    return [
        f"{first}@{domain}", f"{first}.{last}@{domain}", f"{first}_{last}@{domain}",
        f"{first[0]}{last}@{domain}", f"{first}{last}@{domain}"
    ]

# Extract people
def extract_people_info(html):
    soup = BeautifulSoup(html, "html.parser")
    people, emails, linkedins = [], set(), set()

    for tag in soup.find_all(['p', 'div', 'li', 'span', 'a']):
        text = tag.get_text(" ", strip=True)

        # Titles
        for title in TITLE_KEYWORDS:
            if title.lower() in text.lower():
                cleaned = clean_name(text)
                if looks_like_a_name(cleaned):
                    people.append((cleaned, title))

        # Emails
        for match in re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text):
            if is_valid_email(match):
                emails.add(match)

        # LinkedIn
        if "linkedin.com/in/" in text:
            links = re.findall(r"https?://(www\.)?linkedin\.com/in/[^\s\"'>]+", text)
            linkedins.update(links)

    return people, list(emails), list(linkedins)

# Crawl
def crawl_site(base_url):
    visited = set()
    to_visit = [base_url]
    domain = urlparse(base_url).netloc
    all_people, all_emails, all_linkedins = [], [], []

    while to_visit and len(visited) < MAX_PAGES:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
                visited.add(url)
                print(f"🕷️ Crawling: {url}")
                people, emails, linkedins = extract_people_info(res.text)
                all_people.extend(people)
                all_emails.extend(emails)
                all_linkedins.extend(linkedins)

                soup = BeautifulSoup(res.text, "html.parser")
                for link in soup.find_all("a", href=True):
                    href = urljoin(url, link["href"])
                    if urlparse(href).netloc == domain and href not in visited:
                        to_visit.append(href)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            continue

    return all_people, list(set(all_emails)), list(set(all_linkedins))

# Main
def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        website = fields.get("website") or fields.get("website url")
        if not website:
            continue

        norm_url = normalize_url(website)
        people, emails, linkedins = crawl_site(norm_url)

        name, title, email, permutations, backup_email = "", "", "", "", ""
        email_source, email_inferred_from = "", "", ""

        if people:
            name, title = people[0]
            name = clean_name(name)
            domain = urlparse(norm_url).netloc.replace("www.", "")

            # Check if decision maker email exists
            for em in emails:
                if name.split()[0].lower() in em.lower():
                    email = em
                    email_source = "website"
                    break

            # Fallback to permutation logic
            if not email and emails:
                backup_email = emails[0]
                email_source = "guessed"
                permutations = ", ".join(guess_email_permutations(name, domain))
                email_inferred_from = backup_email.split("@")[0]

        # Prepare update payload
        update_data = {
            "Decision Maker Name": name,
            "Decision Maker Title": title,
            "Decision Maker Email": email,
            "LinkedIn URL": linkedins[0] if linkedins else "",
            "Email Source": email_source,
            "Email Permutations": permutations,
            "Backup Email Contact": backup_email,
            "Backup Email Source": "staff" if backup_email else "",
            "Decision Email Inferred From": email_inferred_from
        }

        try:
            airtable.update(record["id"], update_data)
            print(f"✅ Updated: {name or 'No Name'} | {email or permutations or 'No email'}")
            updated += 1
        except Exception as e:
            print(f"❌ Airtable error: {e}")

    print(f"\n🏁 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
