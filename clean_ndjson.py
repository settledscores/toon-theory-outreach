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

output_lines = []

with open(input_path, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue  # skip blank lines

        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Skipping line due to JSON error: {e}")
            continue

        if not entry.get("initial date", "").strip():
            for field in ["email 1", "email 2", "email 3", "use cases"]:
                entry.pop(field, None)

        output_lines.append(json.dumps(entry, ensure_ascii=False))

with open(input_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n")

print("Cleanup complete.")
