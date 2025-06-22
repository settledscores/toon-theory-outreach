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

# ApyHub setup
APYHUB_API_KEY = os.getenv("APYHUB_API_KEY")
APYHUB_ENDPOINT = "https://api.apyhub.com/generate/summarize-text"

HEADERS = {
    "Content-Type": "application/json",
    "apy-token": APYHUB_API_KEY
}

MAX_INPUT_LENGTH = 10000  # Adjust as needed for safety

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]

def summarize_with_apyhub(text):
    try:
        payload = { "text": text }
        response = requests.post(APYHUB_ENDPOINT, headers=HEADERS, json=payload)

        if response.status_code == 200:
            return response.json().get("data", "").strip()
        else:
            print(f"⚠️ ApyHub error: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        print(f"❌ Exception while summarizing: {e}")
        return ""

def update_mini_scrape(record_id, summary):
    airtable.update(record_id, {"mini scrape": summary})

def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        full_text = fields.get("web copy", "")
        mini_scrape = fields.get("mini scrape", "")

        if not full_text or mini_scrape:
            continue

        print(f"🧹 Summarizing for: {fields.get('website', '[no website]')}")

        cleaned = clean_text(full_text)
        truncated = truncate_text(cleaned)
        summary = summarize_with_apyhub(truncated)

        if summary:
            update_mini_scrape(record["id"], summary)
            print("✅ Mini scrape updated")
            updated += 1
        else:
            print("❌ Summary generation failed")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
