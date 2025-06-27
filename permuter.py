import os
from pyairtable import Table
from urllib.parse import urlparse

# Load environment variables
API_KEY = os.environ.get("AIRTABLE_API_KEY")
BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
TABLE_NAME = os.environ.get("SCRAPER_TABLE_NAME")

if not all([API_KEY, BASE_ID, TABLE_NAME]):
    raise ValueError("Missing one or more required environment variables.")

table = Table(API_KEY, BASE_ID, TABLE_NAME)

def extract_domain(url):
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        return domain.lower()
    except:
        return ""

def generate_permutations(first, last, domain):
    first = first.lower().strip()
    last = last.lower().strip()

    return [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last}@{domain}"
    ]

def needs_permutation(record):
    fields = record.get("fields", {})
    return (
        fields.get("First Name") and
        fields.get("Last Name") and
        fields.get("website url") and
        not fields.get("Email Permutations")
    )

def update_record(record):
    fields = record.get("fields", {})
    first = fields["First Name"].strip()
    last = fields["Last Name"].strip()
    website = fields["website url"].strip()

    domain = extract_domain(website)
    if not domain:
        return

    perms = generate_permutations(first, last, domain)
    table.update(record["id"], {
        "Email Permutations": ", ".join(perms)
    })
    print(f"✅ Updated: {first} {last} → {len(perms)} permutations")

def run():
    print("🔍 Fetching records...")
    records = table.all()
    updated = 0

    for record in records:
        if needs_permutation(record):
            update_record(record)
            updated += 1

    print(f"🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    run()
