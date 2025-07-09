import json
import os

leads_path = "leads/scraped_leads.ndjson"

def read_blocks(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()
    return [block.strip() for block in raw.split("\n\n") if block.strip()]

def clean_block(json_str):
    try:
        obj = json.loads(json_str)
        if not obj.get("initial date", "").strip():
            for key in ["email 1", "email 2", "email 3", "use cases"]:
                if key in obj:
                    obj[key] = ""
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        print("⚠️ Skipping invalid JSON block")
        return json_str

def write_blocks(file_path, blocks):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(blocks) + "\n")

# Process
if os.path.exists(leads_path):
    print("🧹 Cleaning scraped_leads.ndjson...")
    blocks = read_blocks(leads_path)
    cleaned_blocks = [clean_block(b) for b in blocks]
    write_blocks(leads_path, cleaned_blocks)
    print("✅ Done. Emails and use cases wiped where initial date is blank.")
else:
    print("❌ leads/scraped_leads.ndjson not found.")
