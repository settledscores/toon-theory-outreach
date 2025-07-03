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

def main():
    print("🔄 Matching verified emails to leads...")
    verified_emails = load_verified_emails()
    verified_map = {
        extract_domain_from_email(email): email
        for email in verified_emails
    }

    updated = 0
    results = []

    with open(SCRAPED_NDJSON, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except:
                continue

            website_url = record.get("website url", "")
            website_domain = extract_domain_from_url(website_url)

            if not record.get("email") and website_domain in verified_map:
                record["email"] = verified_map[website_domain]
                updated += 1

            results.append(record)

    with open(SCRAPED_NDJSON, "w", encoding="utf-8") as f:
        for record in results:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"✅ {updated} emails paired and updated in {SCRAPED_NDJSON}")

if __name__ == "__main__":
    main()
