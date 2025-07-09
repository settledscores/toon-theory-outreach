import json
import shutil
import os

input_path = "leads/scraped_leads.ndjson"
backup_path = "leads/scraped_leads_backup.ndjson"

# Backup the original file
if os.path.exists(input_path):
    shutil.copyfile(input_path, backup_path)
else:
    print(f"File not found: {input_path}")
    exit(1)

def read_multiline_json_blocks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        buffer = []
        brace_count = 0
        for line in f:
            brace_count += line.count("{") - line.count("}")
            buffer.append(line)
            if brace_count == 0 and buffer:
                yield "".join(buffer)
                buffer = []

output_lines = []

for raw_json in read_multiline_json_blocks(input_path):
    try:
        entry = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"Skipping block due to JSON error: {e}")
        continue

    if not entry.get("initial date", "").strip():
        for field in ["email 1", "email 2", "email 3", "use cases"]:
            entry.pop(field, None)

    output_lines.append(json.dumps(entry, ensure_ascii=False, indent=2))

with open(input_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n")

print("Cleanup complete.")
