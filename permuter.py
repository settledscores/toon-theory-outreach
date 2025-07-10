import os
import json
from urllib.parse import urlparse

INPUT_PATH = "leads/new.ndjson"
OUTPUT_PATH = "leads/second.txt"
VERIFIED_PATH = "leads/verified.txt"

def extract_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "").lower()
    except:
        return ""

def generate_permutations(first, last, domain):
    first, last = first.lower(), last.lower()
    return [
        f"{first[0]}.{last}@{domain}",
        f"{first}.{last[0]}@{domain}",
        f"{last}.{first}@{domain}",
        f"{last}@{domain}",
        f"{last}{first[0]}@{domain}",
        f"{first[0]}{last}@{domain}",
        f"{first}{last[0]}@{domain}",
        f"{first[0]}{last[0]}@{domain}"
    ]

def load_verified_domains(path):
    domains = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if "@" in line:
                    domains.add(line.strip().split("@")[-1].lower())
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
                    yield buffer.strip(), json.loads(buffer)
                except Exception as e:
                    print(f"❌ Skipping invalid JSON block: {e}")
                buffer = ""

def main():
    print("📥 Loading leads...")
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Input file not found: {INPUT_PATH}")
        return

    verified_domains = load_verified_domains(VERIFIED_PATH)
    new_permutations = set()
    valid_blocks = []

    stats = {
        "total": 0,
        "skipped_email": 0,
        "skipped_missing_fields": 0,
        "skipped_verified_domain": 0,
        "generated": 0
    }

    for raw_block, record in load_multiline_ndjson(INPUT_PATH):
        stats["total"] += 1

        if not isinstance(record, dict):
            continue

        if record.get("email", "").strip():
            stats["skipped_email"] += 1
            continue

        if not record.get("web copy", "").strip():
            stats["skipped_missing_fields"] += 1
            continue

        first = record.get("first name", "").strip()
        last = record.get("last name", "").strip()
        website = record.get("website url", "").strip()

        if not (first and last and website):
            stats["skipped_missing_fields"] += 1
            continue

        domain = extract_domain(website)
        if not domain:
            stats["skipped_missing_fields"] += 1
            continue

        if domain in verified_domains:
            stats["skipped_verified_domain"] += 1
            continue

        perms = generate_permutations(first, last, domain)
        new_permutations.update(perms)
        valid_blocks.append(raw_block)
        stats["generated"] += len(perms)

    # Overwrite new.ndjson with only valid blocks
    with open(INPUT_PATH, "w", encoding="utf-8") as f:
        if valid_blocks:
            f.write("\n".join(valid_blocks) + "\n")

    # Write new permutations
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(new_permutations)) + "\n")

    print("\n📊 Stats:")
    for k, v in stats.items():
        print(f"   {k.replace('_', ' ').title()}: {v}")

    print(f"\n✅ Saved {len(new_permutations)} permutations to {OUTPUT_PATH}")
    print(f"✅ Cleaned {INPUT_PATH} of invalid/verified leads")

if __name__ == "__main__":
    main()
