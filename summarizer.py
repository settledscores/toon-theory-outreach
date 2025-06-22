import os
import re
import requests
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

TLDR_ENDPOINT = "https://www.tldrthis.com/api/summarize-text"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
}

MAX_INPUT_LENGTH = 10000  # Safer for public summarizers

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]

def postprocess_output(text):
    lines = text.splitlines()
    clean_lines = [line for line in lines if not re.match(r"(?i)^here\s+(is|are)\b", line.strip())]
    return "\n".join(clean_lines).strip()

def summarize_with_tldr(text):
    try:
        response = requests.post(TLDR_ENDPOINT, headers=HEADERS, json={"text": text})
        if response.status_code == 200:
            data = response.json()
            return postprocess_output(data.get("summary", "").strip())
        else:
            print(f"⚠️ TLDR error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"❌ Exception while summarizing: {e}")
        return ""

def update_mini_scrape(record_id, text):
    airtable.update(record_id, {"mini scrape": text})

def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        full_text = fields.get("web copy", "")
        mini_scrape = fields.get("mini scrape", "")

        if not full_text or mini_scrape:
            continue

        print(f"🧹 Cleaning for: {fields.get('website', '[no website]')}")

        cleaned = clean_text(full_text)
        truncated = truncate_text(cleaned)
        summary = summarize_with_tldr(truncated)

        if summary:
            update_mini_scrape(record["id"], summary)
            print("✅ Updated mini scrape")
            updated += 1
        else:
            print("❌ Failed to generate summary")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
