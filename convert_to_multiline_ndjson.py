import os
import json

FLAT_PATH = "leads/scraped_leads.ndjson"
NESTED_PATH = "leads/scraped_leads_nested.ndjson"

def convert_flat_to_nested(flat_path, nested_path):
    if not os.path.exists(flat_path):
        print(f"❌ File not found: {flat_path}")
        return

    count = 0
    with open(flat_path, "r", encoding="utf-8") as fin, open(nested_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                fout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n\n")
                count += 1
            except json.JSONDecodeError as e:
                print(f"❌ Skipped invalid line: {e}")

    print(f"✅ Converted {count} records to nested NDJSON → {nested_path}")

if __name__ == "__main__":
    convert_flat_to_nested(FLAT_PATH, NESTED_PATH)
