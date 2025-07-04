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

    all_permutations = set()

    skipped_with_email = 0
    skipped_missing_fields = 0
    total_processed = 0

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
        all_permutations.update(perms)

    print("\n📊 Stats:")
    print(f"   Total leads processed: {total_processed}")
    print(f"   Skipped (already had email): {skipped_with_email}")
    print(f"   Skipped (missing fields): {skipped_missing_fields}")
    print(f"   Permutations generated: {len(all_permutations)}")

    if not all_permutations:
        print("⚠️ No permutations generated.")
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_permutations)))

    print(f"\n✅ Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
