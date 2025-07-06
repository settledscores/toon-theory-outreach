import os
import json
from urllib.parse import urlparse

INPUT_PATH = "leads/scraped_leads.ndjson"
PERMS_PATH = "leads/permutations.txt"
EMAILS_PATH = "leads/emails.txt"

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

def load_domains_from_perms_and_emails(*paths):
    domains = set()
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "@" in line:
                    domain = line.strip().split("@")[-1].lower()
                    domains.add(domain)
    return domains

def load_multiline_ndjson(path):
    with open(path, "r", encoding="utf-8") as f:
        buffer = ""
        for line in f:
            if line.strip() == "":
                continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    yield json.loads(buffer)
                except Exception as e:
                    print(f"❌ Skipping invalid JSON block: {e}")
                buffer = ""

def main():
    print("📥 Loading scraped leads...")
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Input file not found: {INPUT_PATH}")
        return

    print("📄 Checking previously used domains (permutations + verified emails)...")
    used_domains = load_domains_from_perms_and_emails(PERMS_PATH, EMAILS_PATH)
    new_permutations = set()

    skipped_with_email = 0
    skipped_missing_fields = 0
    skipped_existing_domain = 0
    total_processed = 0
    new_generated = 0

    for record in load_multiline_ndjson(INPUT_PATH):
        if not isinstance(record, dict):
            continue

        total_processed += 1

        company = record.get("company name", "Unknown Company").strip()
        first = record.get("first name", "").strip()
        display_name = first or "Unnamed"
        label = f"{display_name} of {company}"

        if record.get("email", "").strip():
            print(f"⏭️ Skipped {label} (already has email)")
            skipped_with_email += 1
            continue

        if not record.get("web copy", "").strip():
            print(f"⏭️ Skipped {label} (missing web copy)")
            skipped_missing_fields += 1
            continue

        last = record.get("last name", "").strip()
        website = record.get("website url", "").strip()

        if not (first and last and website):
            print(f"⏭️ Skipped {label} (missing name or website)")
            skipped_missing_fields += 1
            continue

        domain = extract_domain(website)
        if not domain:
            print(f"⏭️ Skipped {label} (could not extract domain)")
            skipped_missing_fields += 1
            continue

        if domain in used_domains:
            print(f"⏭️ Skipped {label} (domain already used: {domain})")
            skipped_existing_domain += 1
            continue

        perms = generate_permutations(first, last, domain)
        new_permutations.update(perms)
        used_domains.add(domain)
        new_generated += len(perms)

    print("\n📊 Stats:")
    print(f"   Total leads processed: {total_processed}")
    print(f"   Skipped (already had email): {skipped_with_email}")
    print(f"   Skipped (missing fields): {skipped_missing_fields}")
    print(f"   Skipped (domain already seen): {skipped_existing_domain}")
    print(f"   Permutations generated: {new_generated}")

    if not new_permutations:
        print("⚠️ No new permutations generated.")
        return

    os.makedirs(os.path.dirname(PERMS_PATH), exist_ok=True)
    with open(PERMS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(new_permutations)) + "\n")

    print(f"\n✅ Overwritten {PERMS_PATH} with {new_generated} new permutations")

if __name__ == "__main__":
    main()
