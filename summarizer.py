import os
import re
import requests
from io import BytesIO
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# ApyHub Document Summarizer API
APYHUB_API_KEY = os.getenv("APYHUB_API_KEY")
APYHUB_ENDPOINT = "https://api.apyhub.com/ai/summarize-documents/file"

HEADERS = {
    "apy-token": APYHUB_API_KEY
}

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

def summarize_with_apyhub_doc(text):
    try:
        buffer = BytesIO(text.encode('utf-8'))
        buffer.name = "webcopy.txt"

        files = {
            "file": ("webcopy.txt", buffer, "text/plain")
        }
        data = {
            "summary_length": "medium"
        }

        response = requests.post(APYHUB_ENDPOINT, headers=HEADERS, files=files, data=data)

        if response.status_code == 200:
            return response.json().get("data", "").strip()
        else:
            print(f"⚠️ ApyHub error: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        print(f"❌ Exception during summary: {e}")
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
        summary = summarize_with_apyhub_doc(cleaned)

        if summary:
            update_mini_scrape(record["id"], summary)
            print("✅ Mini scrape updated")
            updated += 1
        else:
            print("❌ Summary generation failed")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
