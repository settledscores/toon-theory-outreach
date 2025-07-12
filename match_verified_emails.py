import os
import json
import re

VERIFIED_TXT = "leads/second.txt"
INPUT_NDJSON = "leads/new.ndjson"  # Input now comes directly from here
OUTPUT_NDJSON = "leads/new.ndjson"  # Output overwrites the same file

def extract_domain_from_email(email):
    return email.split('@')[-1].strip().lower()

def extract_domain_from_url(url):
    if not url:
        return ""
    url = url.lower().strip()
    url = re.sub(r"^https?://", "", url)
    url = url.split("/")[0]
    return url.replace("www.", "")

def load_verified_emails():
    with open(VERIFIED_TXT, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if "@" in line]

def read_ndjson_multiline(path):
    results = []
    buffer = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            buffer += line
            if line.strip() == "}":
                try:
                    obj = json.loads(buffer)
                    results.append(obj)
                except Exception as e:
                    print(f"❌ Skipping invalid block: {e}")
                buffer = ""
    return results

def write_ndjson_multiline(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, indent=2, ensure_ascii=False)
            f.write("\n")

def main():
    print("🔄 Matching verified emails to leads...")
    verified_emails = load_verified_emails()
    verified_map = {
        extract_domain_from_email(email): email
        for email in verified_emails
    }

    updated = 0
    kept = 0
    records = read_ndjson_multiline(INPUT_NDJSON)
    output = []

    for record in records:
        website_url = record.get("website url", "")
        website_domain = extract_domain_from_url(website_url)

        if website_domain in verified_map:
            if not record.get("email"):
                record["email"] = verified_map[website_domain]
                updated += 1
            output.append(record)
            kept += 1
        else:
            print(f"🗑️ Removed block — domain '{website_domain}' not in verified list")

    write_ndjson_multiline(OUTPUT_NDJSON, output)

    print(f"✅ {updated} emails paired")
    print(f"📦 {kept} total records kept")
    print(f"📝 Output written to {OUTPUT_NDJSON}")

if __name__ == "__main__":
    main()
