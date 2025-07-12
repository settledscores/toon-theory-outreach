import json

FILE_PATH = "leads/scraped_leads.ndjson"
FIELDS_TO_CLEAR = ["use cases", "services", "email 1", "email 2", "email 3"]

def read_multiline_ndjson(path):
    records = []
    buffer = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    records.append(json.loads(buffer))
                except Exception as e:
                    print(f"❌ Invalid JSON block: {e}")
                buffer = ""
    return records

def write_multiline_ndjson(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, indent=2, ensure_ascii=False))
            f.write("\n\n")

def process_leads(records):
    modified = 0
    for record in records:
        initial_date = record.get("initial date", "").strip()
        if not initial_date:
            for field in FIELDS_TO_CLEAR:
                record[field] = ""
            modified += 1
    return records, modified

def main():
    leads = read_multiline_ndjson(FILE_PATH)
    updated_leads, count = process_leads(leads)
    write_multiline_ndjson(FILE_PATH, updated_leads)
    print(f"✅ Cleared fields for {count} leads missing 'initial date'")
    print(f"💾 Saved to {FILE_PATH}")

if __name__ == "__main__":
    main()
