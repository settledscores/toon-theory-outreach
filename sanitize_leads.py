import json

FILE_PATH = "leads/scraped_leads.ndjson"

FIELDS_TO_STRIP = [
    "message id", "message id 2", "message id 3",
    "in-reply-to 1", "in-reply-to 2", "in-reply-to 3",
    "references 1", "references 2", "references 3"
]

def sanitize_leads(file_path):
    buffer = ""
    cleaned = []
    modified = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            buffer += line
            if line.endswith("}"):
                try:
                    obj = json.loads(buffer)
                    original = obj.copy()
                    for field in FIELDS_TO_STRIP:
                        if field in obj and obj[field] == "":
                            del obj[field]
                    if obj != original:
                        modified += 1
                    cleaned.append(obj)
                except json.JSONDecodeError as e:
                    print("⚠️ Invalid JSON block:\n", buffer, "\nError:", e)
                buffer = ""

    with open(file_path, "w", encoding="utf-8") as f:
        for entry in cleaned:
            f.write(json.dumps(entry, indent=2, ensure_ascii=False) + "\n\n")

    print(f"\n✅ Sanitized {modified} blocks (stripped empty threading fields).\n")

if __name__ == "__main__":
    sanitize_leads(FILE_PATH)
