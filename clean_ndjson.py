import json
import shutil
import os

input_path = "leads/scraped_leads.ndjson"
backup_path = "leads/scraped_leads_backup.ndjson"

# Backup original file
if os.path.exists(input_path):
    shutil.copyfile(input_path, backup_path)
else:
    print(f"File not found: {input_path}")
    exit(1)

def read_multiline_json_blocks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        buffer = []
        brace_level = 0
        for line in f:
            brace_level += line.count('{') - line.count('}')
            buffer.append(line)
            if brace_level == 0 and buffer:
                yield ''.join(buffer)
                buffer = []

output_blocks = []

for block in read_multiline_json_blocks(input_path):
    try:
        obj = json.loads(block)
    except json.JSONDecodeError as e:
        print(f"Skipping block due to JSON error: {e}")
        continue

    if not obj.get("initial date", "").strip():
        for field in ["email 1", "email 2", "email 3", "use cases"]:
            if field in obj:
                obj[field] = ""

    output_blocks.append(json.dumps(obj, indent=2, ensure_ascii=False))

with open(input_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_blocks) + "\n")

print("✅ Fields wiped (not removed) where 'initial date' is blank.")
