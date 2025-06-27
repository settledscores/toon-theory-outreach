import os
import requests
from urllib.parse import urlparse

# Load secrets from environment
API_KEY = os.environ.get("NOCODB_API_KEY")
BASE_URL = os.environ.get("NOCODB_BASE_URL")
TABLE_ID = os.environ.get("NOCODB_SCRAPER_TABLE_ID")

if not all([API_KEY, BASE_URL, TABLE_ID]):
    raise ValueError("Missing one or more required environment variables.")

HEADERS = {
    "xc-token": API_KEY,
    "Content-Type": "application/json"
}

def extract_domain(url):
    try:
        domain = urlparse(url).netloc or urlparse(url).path
        return domain.replace("www.", "").lower()
    except:
        return ""

def generate_permutations(first, last, domain):
    first = first.lower()
    last = last.lower()
    return [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}"
    ]

def needs_permutation(record):
    return (
        record.get("First Name") and
        record.get("Last Name") and
        record.get("website url") and
        not record.get("Email Permutations")
    )

def fetch_records():
    url = f"{BASE_URL}/api/v2/tables/{TABLE_ID}/records?limit=10000"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    records = response.json().get("list", [])

    if records:
        print("\n🧪 Sample record:")
        print(records[0])
        print("\n🔑 Keys in first record:", list(records[0].keys()))
        print("📌 Record ID (used for PATCH):", records[0].get("id"))

    return records

def update_record(record_id, permutations):
    url = f"{BASE_URL}/api/v2/tables/{TABLE_ID}/records/{record_id}"
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
        if not needs_permutation(record):
            continue

        first = record["First Name"].strip()
        last = record["Last Name"].strip()
        website = record["website url"].strip()
        domain = extract_domain(website)

        if not domain:
            continue

        record_id = record.get("id")
        if not record_id:
            print(f"⚠️ Skipping record with no 'id': {record}")
            continue

        perms = generate_permutations(first, last, domain)
        update_record(record_id, perms)
        print(f"✅ Updated: {first} {last} → {len(perms)} permutations")
        updated += 1

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    run()
