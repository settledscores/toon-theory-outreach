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
    removed_partial = 0

    for record in records:
        email = record.get("email", "").strip()
        web_copy = record.get("web copy", "").strip()

        # Keep if both email and web copy are present
        if email and web_copy:
            filtered.append(record)
        # Keep if both email and web copy are missing (website url is always present)
        elif not email and not web_copy:
            filtered.append(record)
        # Remove if only one of them is present
        else:
            removed_partial += 1

    print(f"🧹 Removed {removed_partial} leads with partial email/web copy")
    print(f"💾 Saving {len(filtered)} eligible leads...")

    write_ndjson(filtered, TEMP_PATH)
    os.replace(TEMP_PATH, INPUT_PATH)
    print("✅ Done.")

if __name__ == "__main__":
    filter_leads()
