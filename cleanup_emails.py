# cleanup_emails.py

import json
import os

LEADS_PATH = os.path.join("leads", "scraped_leads.ndjson")

def load_pretty_ndjson(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
    leads = []
    for block in blocks:
        try:
            leads.append(json.loads(block))
        except json.JSONDecodeError:
            print("⚠ Skipping invalid JSON block")
    return leads

def save_pretty_ndjson(filepath, records):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n\n".join(json.dumps(r, indent=2) for r in records))
        f.write("\n")

def clean_fields_if_no_initial_date(leads):
    modified = 0
    for lead in leads:
        if not lead.get("initial date", "").strip():
            for field in ["email 1", "email 2", "email 3", "services"]:
                if field in lead:
                    lead[field] = ""
                    modified += 1
    return modified

def main():
    if not os.path.exists(LEADS_PATH):
        print("❌ leads/scraped_leads.ndjson not found")
        return

    leads = load_pretty_ndjson(LEADS_PATH)
    modified = clean_fields_if_no_initial_date(leads)
    save_pretty_ndjson(LEADS_PATH, leads)
    print(f"✅ Cleaned {modified} fields and saved to {LEADS_PATH}")

if __name__ == "__main__":
    main()
