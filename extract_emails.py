import os
import json
import re
from urllib.parse import urlparse

INPUT_PATH = "leads/scraped_leads.ndjson"
OUTPUT_PATH = "leads/emails.txt"

def extract_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        return domain.replace("www.", "").lower()
    except:
        return ""

def extract_emails(text):
    # Very loose regex to pick up even obfuscated variants
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)

def is_match(email, domain, first, last):
    if not email.endswith("@" + domain):
        return False
    local = email.split("@")[0].lower()
    return first.lower() in local or last.lower() in local

def read_multiline_ndjson(path):
    with open(path, "r", encoding="utf-8") as f:
        buffer = ""
        for line in f:
            if line.strip() == "":
                continue
            buffer += line
            if line.strip().endswith("}"):
                try:
                    yield json.loads(buffer)
                except Exception as e:
                    print(f"❌ Skipping invalid JSON block: {e}")
                buffer = ""

def main():
    print("📥 Loading leads...")
    if not os.path.exists(INPUT_PATH):
        print(f"❌ Input file not found: {INPUT_PATH}")
        return

    matches = set()
    total_checked = 0
    total_matched = 0

    for record in read_multiline_ndjson(INPUT_PATH):
        first = record.get("first name", "").strip().lower()
        last = record.get("last name", "").strip().lower()
        domain = extract_domain(record.get("website url", ""))
        text = record.get("web copy", "")

        if not (first and last and domain and text):
            continue

        total_checked += 1
        found_emails = extract_emails(text)

        for email in found_emails:
            if is_match(email, domain, first, last):
                matches.add(email.lower())
                total_matched += 1
                break  # one match per record is enough

    if not matches:
        print("⚠️ No valid emails found.")
        return

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(matches)) + "\n")

    print(f"✅ Extracted {len(matches)} valid emails from {total_checked} eligible leads.")
    print(f"📄 Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
