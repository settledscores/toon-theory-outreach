import os
import requests
from urllib.parse import urlparse

# Load environment variables
API_KEY = os.environ.get("NOCODB_API_KEY")
BASE_URL = os.environ.get("NOCODB_BASE_URL")
TABLE_NAME = os.environ.get("NOCODB_SCRAPER_TABLE_ID")  # This is now the table *name*, not hash

if not all([API_KEY, BASE_URL, TABLE_NAME]):
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
    url = f"{BASE_URL}/api/v2/tables/{TABLE_NAME}/records?limit=10000"
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
        print("📌 Record ID (used for PATCH):", records[0].get("id"))

    return records

def needs_permutation(record):
    return (
        record.get("First Name") and
        record.get("Last Name") and
        record.get("website url") and
        not record.get("Email Permutations")
    )

def update_record(record_id, permutations):
    url = f"{BASE_URL}/api/v2/tables/{TABLE_NAME}/records/{record_id}"
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
        record_id = record.get("id")
        if not record_id:
            print(f"⚠️ Skipping record with no 'id': {record}")
            continue

        if not needs_permutation(record):
            continue

        first = record["First Name"].strip()
        last = record["Last Name"].strip()
        website = record["website url"].strip()
        domain = extract_domain(website)

        if not domain:
            print(f"⚠️ Could not extract domain from: {website}")
            continue

        permutations = generate_permutations(first, last, domain)
        update_record(record_id, permutations)
        print(f"✅ Updated: {first} {last} → {len(permutations)} permutations")
        updated += 1

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    run()
