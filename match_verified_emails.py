import os
import json
import re

VERIFIED_TXT = "leads/verified.txt"
SCRAPED_JSON = "leads/scraped_leads.ndjson"

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

def load_json_leads():
    with open(SCRAPED_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_leads(data):
    with open(SCRAPED_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    verified_emails = load_verified_emails()
    verified_map = {
        extract_domain_from_email(email): email
        for email in verified_emails
    }

    json_data = load_json_leads()
    leads = json_data.get("records", [])
    updated = 0

    for lead in leads:
        website_url = lead.get("website url", "")
        website_domain = extract_domain_from_url(website_url)

        if not lead.get("email") and website_domain in verified_map:
            lead["email"] = verified_map[website_domain]
            updated += 1

    json_data["records"] = leads
    save_json_leads(json_data)
    print(f"✅ {updated} emails paired and updated in {SCRAPED_JSON}")

if __name__ == "__main__":
    main()
