import json

FILE_PATH = "leads/scraped_leads.ndjson"

def sanitize_ndjson(file_path):
    buffer = ""
    sanitized = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            buffer += line
            if line.endswith("}"):
                try:
                    obj = json.loads(buffer)
                    website = obj.get("website url")
                    if website:
                        print(f"✔ Keeping: {website}")
                        sanitized.append({"website url": website})
                    else:
                        print("⛔ No website url in object, skipping.")
                except json.JSONDecodeError as e:
                    print("⚠️ Failed to parse block:\n", buffer, "\nError:", e)
                buffer = ""

    # Overwrite the original file
    with open(file_path, "w", encoding="utf-8") as f:
        for entry in sanitized:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\n✅ Sanitized {len(sanitized)} entries.")

if __name__ == "__main__":
    sanitize_ndjson(FILE_PATH)
