import json
import os

INPUT_PATH = "leads/scraped_leads.ndjson"
TEMP_PATH = "leads/scraped_leads.filtered.ndjson"

def read_multiline_ndjson(path):
    buffer, records = "", []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            buffer += line
            if line.strip() == "}":
                try:
                    records.append(json.loads(buffer))
                except Exception as e:
                    print(f"❌ Skipping invalid record: {e}")
                buffer = ""
    return records

def write_ndjson(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            json.dump(record, f, ensure_ascii=False, indent=2)
            f.write("\n")

def filter_leads():
    print("🔍 Loading leads...")
    records = read_multiline_ndjson(INPUT_PATH)

    filtered = []
    removed_missing_web_copy = 0
    removed_missing_email = 0

    for record in records:
        web_copy = record.get("web copy", "")
        email = record.get("email", "")

        if not web_copy or not web_copy.strip():
            removed_missing_web_copy += 1
            continue

        if not email or not email.strip():
            removed_missing_email += 1
            continue

        filtered.append(record)

    print(f"🧹 Removed {removed_missing_web_copy} leads missing 'web copy'")
    print(f"🧹 Removed {removed_missing_email} leads missing 'email'")
    print(f"💾 Saving {len(filtered)} eligible leads...")

    write_ndjson(filtered, TEMP_PATH)
    os.replace(TEMP_PATH, INPUT_PATH)
    print("✅ Done.")

if __name__ == "__main__":
    filter_leads()
