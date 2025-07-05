import os
import json
from urllib.parse import urlparse

INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/permutations.txt"

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

def load_existing_permutations(path):
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip().lower() for line in f if line.strip())

def load_multiline_ndjson(path):
    """Supports pretty-formatted NDJSON with objects spanning multiple lines."""
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

    print("📄 Loading existing permutations...")
    existing_permutations = load_existing_permutations(OUTPUT_PATH)
    all_permutations = set(existing_permutations)

    skipped_with_email = 0
    skipped_missing_fields = 0
    skipped_existing = 0
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

        perms = generate_permutations(first, last, domain)
        fresh_perms = [p for p in perms if p not in existing_permutations]

        if not fresh_perms:
            skipped_existing += 1
            print(f"⏭️ Skipped {label} (all permutations already exist)")
            continue

        all_permutations.update(fresh_perms)
        new_generated += len(fresh_perms)

    print("\n📊 Stats:")
    print(f"   Total leads processed: {total_processed}")
    print(f"   Skipped (already had email): {skipped_with_email}")
    print(f"   Skipped (missing fields): {skipped_missing_fields}")
    print(f"   Skipped (no new permutations): {skipped_existing}")
    print(f"   New permutations added: {new_generated}")
    print(f"   Total permutations after merge: {len(all_permutations)}")

    if not new_generated:
        print("⚠️ No new permutations to write.")
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_permutations)) + "\n")

    print(f"\n✅ Overwritten {OUTPUT_PATH} with merged set")

if __name__ == "__main__":
    main()
