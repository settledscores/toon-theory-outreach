import os
import json
from urllib.parse import urlparse

INPUT_PATH = "leads/scraped_leads.json"
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

def main():
    print("📥 Loading scraped leads...")
    records = []

    try:
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            buffer = ""
            for line in f:
                if line.strip() == "":
                    continue
                buffer += line
                if line.strip() == "}":
                    try:
                        record = json.loads(buffer)
                        records.append(record)
                    except Exception as e:
                        print(f"❌ Skipping invalid JSON block: {e}")
                    buffer = ""
    except Exception as e:
        print(f"❌ Failed to read scraped_leads.json: {e}")
        return

    all_permutations = set()

    for record in records:
        if not record.get("web copy", "").strip():
            continue  # ❌ Skip if 'web copy' is empty or missing

        first = record.get("first name", "").strip()
        last = record.get("last name", "").strip()
        website = record.get("website url", "").strip()

        if not (first and last and website):
            continue

        domain = extract_domain(website)
        if not domain:
            continue

        perms = generate_permutations(first, last, domain)
        all_permutations.update(perms)

    if not all_permutations:
        print("⚠️ No permutations generated.")
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(all_permutations)))

    print(f"✅ Saved {len(all_permutations)} permutations to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
