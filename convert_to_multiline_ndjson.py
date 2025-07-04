import os
import json
import re

FLAT_PATH = "leads/scraped_leads.ndjson"
NESTED_PATH = "leads/scraped_leads_nested.ndjson"

def repair_ndjson(raw_text):
    blocks = re.findall(r'{.*?}\s*(?=\n{|\Z)', raw_text, flags=re.DOTALL)
    repaired = []
    skipped = 0

    for i, block in enumerate(blocks):
        try:
            obj = json.loads(block)
            repaired.append(obj)
        except json.JSONDecodeError as e:
            print(f"❌ Skipped malformed block #{i+1}: {e}")
            skipped += 1

    return repaired, skipped

def convert_flat_to_nested(flat_path, nested_path):
    if not os.path.exists(flat_path):
        print(f"❌ File not found: {flat_path}")
        return

    with open(flat_path, "r", encoding="utf-8") as f:
        raw = f.read()

    records, skipped = repair_ndjson(raw)

    with open(nested_path, "w", encoding="utf-8") as fout:
        for obj in records:
            fout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n\n")

    print(f"✅ Converted {len(records)} records to nested NDJSON → {nested_path}")
    if skipped:
        print(f"⚠️ Skipped {skipped} malformed block(s)")

if __name__ == "__main__":
    convert_flat_to_nested(FLAT_PATH, NESTED_PATH)
