import json
import os

leads_path = os.path.join("leads", "scraped_leads.ndjson")

def clean_leads(path):
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = [b.strip() for b in content.strip().split("\n\n") if b.strip()]
    cleaned_blocks = []

    for block in blocks:
        try:
            record = json.loads(block)

            if not record.get("initial date", "").strip():
                record.pop("email 1", None)
                record.pop("email 2", None)
                record.pop("email 3", None)

            cleaned_blocks.append(json.dumps(record, indent=2))
        except json.JSONDecodeError:
            print("⚠ Skipping invalid JSON block")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(cleaned_blocks) + "\n")

    print(f"✅ Cleaned {len(cleaned_blocks)} leads and saved to {path}")

if __name__ == "__main__":
    clean_leads(leads_path)
