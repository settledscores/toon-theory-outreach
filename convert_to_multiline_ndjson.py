import os
import json
import re

FLAT_PATH = "leads/scraped_leads.ndjson"
NESTED_PATH = "leads/scraped_leads_nested.ndjson"

# Deprecated fields to remove
DEPRECATED_FIELDS = {
    "message id", "message id 2", "message id 3",
    "use cases", "services"
}

# Fields that may contain whitespace-only strings to normalize
WHITESPACE_FIELDS = [
    "first name", "last name", "middle name", "title", "email",
    "web copy", "email 1", "email 2", "email 3",
    "initial date", "follow-up 1 date", "follow-up 2 date", "reply"
]

def attempt_repair(text):
    # Remove trailing commas before closing braces/brackets
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Ensure all keys and string values are quoted
    def fix_quotes(match):
        key, val = match.group(1).strip(), match.group(2).strip()
        key = f'"{key}"' if not key.startswith('"') else key
        val = val.strip('"')
        val = f'"{val}"' if not val.startswith('"') and not val.lower() in ("true", "false", "null") and not re.match(r'^-?\d+(\.\d+)?$', val) else val
        return f"{key}: {val}"

    text = re.sub(r"([a-zA-Z0-9 _\-]+)\s*:\s*([^,\n]+)", fix_quotes, text)

    return text

def repair_ndjson(raw_text):
    blocks = re.findall(r'{.*?}\s*(?=\n{|\Z)', raw_text, flags=re.DOTALL)
    repaired = []
    skipped = 0
    whitespace_fixes = []

    for i, block in enumerate(blocks):
        original = block
        block = attempt_repair(block)

        try:
            obj = json.loads(block)

            # Remove deprecated fields
            for key in list(obj.keys()):
                if key in DEPRECATED_FIELDS:
                    del obj[key]

            # Normalize whitespace-only fields
            for field in WHITESPACE_FIELDS:
                val = obj.get(field, None)
                if isinstance(val, str) and val.strip() == "":
                    if val != "":
                        whitespace_fixes.append({
                            "record": i + 1,
                            "field": field,
                            "business name": obj.get("business name", "(unknown)")
                        })
                    obj[field] = ""

            repaired.append(obj)

        except json.JSONDecodeError as e:
            print(f"❌ Skipped block #{i+1}: {e}")
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
        print(f"⚠️ Skipped {skipped} unrecoverable block(s)")

    if whitespace_fixes:
        print(f"🧼 Fixed {len(whitespace_fixes)} whitespace-only field(s):")
        for fix in whitespace_fixes:
            print(f"   - Record #{fix['record']}: “{fix['field']}” in {fix['business name']}")
    else:
        print("✅ No whitespace-only fields detected.")

if __name__ == "__main__":
    convert_flat_to_nested(FLAT_PATH, NESTED_PATH)
