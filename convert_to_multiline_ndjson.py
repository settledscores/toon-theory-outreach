import os
import json
import re

FLAT_PATH = "leads/scraped_leads.ndjson"
NESTED_PATH = "leads/scraped_leads_nested.ndjson"

# Fields to sanitize
WHITESPACE_FIELDS = [
    "first name", "last name", "middle name", "title", "email",
    "web copy", "use cases", "services", "email 1", "email 2", "email 3",
    "message id", "message id 2", "message id 3",
    "initial date", "follow-up 1 date", "follow-up 2 date", "reply"
]

def repair_ndjson(raw_text):
    blocks = re.findall(r'{.*?}\s*(?=\n{|\Z)', raw_text, flags=re.DOTALL)
    repaired = []
    skipped = 0
    whitespace_fixes = []

    for i, block in enumerate(blocks):
        try:
            obj = json.loads(block)

            # Identify and fix whitespace-only fields
            for field in WHITESPACE_FIELDS:
                val = obj.get(field, None)
                if isinstance(val, str) and val.strip() == "":
                    if val != "":
                        whitespace_fixes.append({
                            "record": i + 1,
                            "field": field,
                            "business name": obj.get("business name", "(unknown)")
                        })
                    obj[field] = ""  # normalize to empty string

            repaired.append(obj)

        except json.JSONDecodeError as e:
            print(f"❌ Skipped malformed block #{i+1}: {e}")
            skipped += 1

    return repaired, skipped, whitespace_fixes

def convert_flat_to_nested(flat_path, nested_path):
    if not os.path.exists(flat_path):
        print(f"❌ File not found: {flat_path}")
        return

    with open(flat_path, "r", encoding="utf-8") as f:
        raw = f.read()

    records, skipped, whitespace_fixes = repair_ndjson(raw)

    with open(nested_path, "w", encoding="utf-8") as fout:
        for obj in records:
            fout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n\n")

    print(f"✅ Converted {len(records)} records to nested NDJSON → {nested_path}")
    if skipped:
        print(f"⚠️ Skipped {skipped} malformed block(s)")

    if whitespace_fixes:
        print(f"🧼 Fixed {len(whitespace_fixes)} whitespace-only field(s):")
        for fix in whitespace_fixes:
            print(f"   - Record #{fix['record']}: “{fix['field']}” in {fix['business name']}")
    else:
        print("✅ No whitespace-only fields detected.")

if __name__ == "__main__":
    convert_flat_to_nested(FLAT_PATH, NESTED_PATH)
