import os
import re
import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# NocoDB setup
API_KEY = os.getenv("NOCODB_API_KEY")
BASE_URL = os.getenv("NOCODB_BASE_URL").rstrip("/")
PROJECT_ID = os.getenv("NOCODB_PROJECT_ID")
TABLE_ID = os.getenv("NOCODB_OUTREACH_TABLE_ID")

HEADERS = {
    "xc-token": API_KEY,
    "Content-Type": "application/json"
}

# Groq setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_INPUT_LENGTH = 14000  # Leave space for prompt+response


def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()


def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]


def generate_prompt(cleaned_text):
    return f"""Remove any irrelevant, duplicate, or filler content from the following text. Do not summarize. Return only the cleaned-up content, with no explanation, no labels, and no intro/outro.

{cleaned_text}
"""


def postprocess_output(text):
    # Remove any leftover "Here is..." or similar model artifacts
    lines = text.splitlines()
    clean_lines = [line for line in lines if not re.match(r"(?i)^here\\s+(is|are)\\b", line.strip())]
    return "\n".join(clean_lines).strip()


def fetch_records():
    url = f"{BASE_URL}/api/v1/db/data/{PROJECT_ID}/{TABLE_ID}?limit=200"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()["list"]


def update_mini_scrape(record_id, text):
    url = f"{BASE_URL}/api/v1/db/data/{PROJECT_ID}/{TABLE_ID}/{record_id}"
    payload = {
        "mini scrape": text
    }
    res = requests.patch(url, headers=HEADERS, json=payload)
    res.raise_for_status()


def main():
    print("🧹 Cleaning web copy for mini scrape...")
    records = fetch_records()
    updated = 0

    for record in records:
        full_text = record.get("web copy", "")
        mini_scrape = record.get("mini scrape", "")
        website = record.get("website", "[no website]")

        if not full_text or mini_scrape:
            continue

        print(f"🧹 Cleaning for: {website}")

        cleaned = clean_text(full_text)
        truncated = truncate_text(cleaned)
        prompt = generate_prompt(truncated)

        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            cleaned_output = postprocess_output(response.choices[0].message.content.strip())
            update_mini_scrape(record["id"], cleaned_output)
            updated += 1
            print("✅ Updated mini scrape")
        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated} records updated.")


if __name__ == "__main__":
    main()
