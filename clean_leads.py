import json
import os

LEADS_FILE = "leads/scraped_leads.ndjson"
TEMP_FILE = "leads/scraped_leads.cleaned.ndjson"

UNNEEDED_FIELDS = [
    "in-reply-to 1", "in-reply-to 2", "in-reply-to 3",
    "references 1", "references 2", "references 3",
    "message id", "message id 2", "message id 3"
]

def read_multiline_ndjson(path):
    records, buffer = [], ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    records.append(json.loads(buffer))
                except Exception as e:
                    print(f"❌ Failed to parse record:\n{buffer}\n→ {e}")
                buffer = ""
    return records

def write_multiline_ndjson(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, ensure_ascii=False, indent=2)
            f.write("\n")

def clean_leads():
    leads = read_multiline_ndjson(LEADS_FILE)
    for lead in leads:
        for key in UNNEEDED_FIELDS:
            if key in lead:
                del lead[key]
    write_multiline_ndjson(TEMP_FILE, leads)
    os.replace(TEMP_FILE, LEADS_FILE)
    print(f"✅ Cleaned and saved {len(leads)} leads.")

if __name__ == "__main__":
    clean_leads()
