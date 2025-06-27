import os
import requests
from urllib.parse import urlparse

# Load secrets from environment
API_KEY = os.environ.get("NOCODB_API_KEY")
BASE_URL = os.environ.get("NOCODB_BASE_URL")
PROJECT_ID = os.environ.get("NOCODB_PROJECT_ID")      # e.g., 'wbv4do3x'
TABLE_ID = os.environ.get("NOCODB_SCRAPER_TABLE_ID")  # e.g., 'muom3qfddoeroow'

if not all([API_KEY, BASE_URL, PROJECT_ID, TABLE_ID]):
    raise ValueError("❌ Missing one or more required environment variables.")

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
    return [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}"
    ]

def fetch_records():
    url = f"{BASE_URL}/api/v1/db/data/noco/{PROJECT_ID}/{TABLE_ID}?limit=10000"
    print(f"\n🚀 URL used for fetch: {url}")
    response = requests.get(url, headers=HEADERS)
    if not response.ok:
        print(f"❌ Failed to fetch records: {response.status_code} — {response.text}")
    response.raise_for_status()
    records = response.json().get("list", [])

    if records:
        print("\n🧪 Sample record:")
        print(records[0])
        print("\n🔑 Keys in first record:", list(records[0].keys()))
        print("📌 Record ID (used for PATCH):", records[0].get("Id"))

    return records

def needs_permutation(record):
    return (
        record.get("First Name") and
        record.get("Last Name") and
        record.get("website url") and
        not record.get("Email Permutations")
    )

def update_record(record_id, permutations):
    url = f"{BASE_URL}/api/v1/db/data/noco/{PROJECT_ID}/{TABLE_ID}/{record_id}"
    data = {
        "Email Permutations": ", ".join(permutations)
    }
    response = requests.patch(url, headers=HEADERS, json=data)
    if not response.ok:
        print(f"❌ Failed to update record {record_id}: {response.status_code} — {response.text}")
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
        record_id = record.get("Id")  # NocoDB uses "Id" for primary key

        if not website or not record_id:
            print(f"⚠️ Skipping record with no website or ID: {record}")
            continue

        domain = extract_domain(website)
        if not domain:
            print(f"⚠️ Skipping invalid domain for record ID {record_id}")
            continue

        permutations = generate_permutations(first, last, domain)
        update_record(record_id, permutations)
        print(f"✅ Updated: {first} {last} → {len(permutations)} permutations")
        updated += 1

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    run()
