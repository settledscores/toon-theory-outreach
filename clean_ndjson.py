import json
import shutil
import os

input_path = "leads/scraped_leads.ndjson"
backup_path = "leads/scraped_leads_backup.ndjson"

# Backup the file
if os.path.exists(input_path):
    shutil.copyfile(input_path, backup_path)
else:
    print(f"❌ File not found: {input_path}")
    exit(1)

def parse_json_objects(file_path):
    """
    Yield individual JSON objects from a file with multiple multi-line JSON entries.
    """
    buffer = ""
    brace_count = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            brace_count += line.count("{") - line.count("}")
            buffer += line
            if brace_count == 0 and buffer.strip():
                yield buffer
                buffer = ""

output_blocks = []

for block in parse_json_objects(input_path):
    try:
        obj = json.loads(block)
    except json.JSONDecodeError as e:
        print(f"❌ Skipping block due to JSON error: {e}")
        continue

    # Only wipe fields if initial date is missing or blank
    if not obj.get("initial date", "").strip():
        for field in ["email 1", "email 2", "email 3", "use cases"]:
            if field in obj:
                obj[field] = ""

    output_blocks.append(json.dumps(obj, ensure_ascii=False, indent=2))

# Write the cleaned output
with open(input_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_blocks) + "\n")

print("✅ Done: Fields wiped if 'initial date' was blank. No blocks deleted.")
