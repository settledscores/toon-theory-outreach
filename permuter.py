import os
import requests
from urllib.parse import urlparse

# Load secrets from environment
API_KEY = os.environ.get("NOCODB_API_KEY")
BASE_URL = os.environ.get("NOCODB_BASE_URL")
PROJECT_ID = os.environ.get("NOCODB_PROJECT_ID")
TABLE_ID = os.environ.get("NOCODB_SCRAPER_TABLE_ID")

if not all([API_KEY, BASE_URL, PROJECT_ID, TABLE_ID]):
    raise ValueError("Missing one or more required environment variables.")

HEADERS = {
    "xc-token": API_KEY,
    "Content-Type": "application/json"
}

def extract_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "").lower()
    except:
        return ""

def generate_permutations(first, last, domain):
    first = first.lower()
    last = last.lower()
    f = first[0]
    return [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}"
    ]

def fetch_records():
    url = f"{BASE_URL}/api/v1/db/data/noco/{PROJECT_ID}/{TABLE_ID}?limit=10000"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json().get("list", [])

def update_record(record_id, permutations):
    url = f"{BASE_URL}/api/v1/db/data/noco/{PROJECT_ID}/{TABLE_ID}/{record_id}"
    data = {
        "Email Permutations": ", ".join(permutations)
    }
    response = requests.patch(url, headers=HEADERS, json=data)
    response.raise_for_status()

def run():
    print("🔍 Fetching records...")
    records = fetch_records()
    updated = 0

    for record in records:
        first = record.get("First Name", "").strip()
        last = record.get("Last Name", "").strip()
        website = record.get("website url", "").strip()
        existing = record.get("Email Permutations")

        if not first or not last or not website or existing:
            continue

        domain = extract_domain(website)
        if not domain:
            continue

        permutations = generate_permutations(first, last, domain)
        update_record(record["Id"], permutations)
        print(f"✅ Updated: {first} {last} → {len(permutations)} permutations")
        updated += 1

    print(f"🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    run()
