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

def purge_fields(leads):
    modified = 0
    for lead in leads:
        for field in ["use cases", "services"]:
            if field in lead:
                del lead[field]
                modified += 1
        if "web copy" in lead:
            lead["web copy"] = ""
            modified += 1
    return modified

def main():
    if not os.path.exists(LEADS_PATH):
        print("❌ leads/scraped_leads.ndjson not found")
        return

    leads = load_pretty_ndjson(LEADS_PATH)
    modified = purge_fields(leads)
    save_pretty_ndjson(LEADS_PATH, leads)
    print(f"✅ Removed fields from {modified} locations and saved to {LEADS_PATH}")

if __name__ == "__main__":
    main()
