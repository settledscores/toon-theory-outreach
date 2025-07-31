import json

INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/scraped_leads.ndjson"

def read_pretty_ndjson(path):
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
                    print(f"Error parsing block: {e}")
                buffer = ""
    return records

def write_pretty_ndjson(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, indent=2))
            f.write("\n\n")

def clean_emails(records):
    for block in records:
        if list(block.keys()) == ["website url"]:
            continue  # untouched
        if "initial date" in block and block["initial date"].strip():
            continue  # keep as-is
        # Clear email fields
        for field in ["email", "email 1", "email 2", "email 3"]:
            if field in block:
                block[field] = ""
    return records

if __name__ == "__main__":
    data = read_pretty_ndjson(INPUT_PATH)
    updated = clean_emails(data)
    write_pretty_ndjson(OUTPUT_PATH, updated)
    print("[✓] Email fields cleared for blocks without 'initial date'.")
