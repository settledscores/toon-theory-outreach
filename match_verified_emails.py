import os
import json
import re

VERIFIED_TXT = "leads/verified.txt"
SCRAPED_NDJSON = "leads/scraped_leads.ndjson"

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
    results = read_ndjson_multiline(SCRAPED_NDJSON)

    for record in results:
        website_url = record.get("website url", "")
        website_domain = extract_domain_from_url(website_url)

        if not record.get("email") and website_domain in verified_map:
            record["email"] = verified_map[website_domain]
            updated += 1

    write_ndjson_multiline(SCRAPED_NDJSON, results)
    print(f"✅ {updated} emails paired and updated in {SCRAPED_NDJSON}")

if __name__ == "__main__":
    main()
