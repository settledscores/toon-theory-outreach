import os
import re
import time
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


def postprocess_output(text):
    lines = text.splitlines()
    return "\n".join([
        line for line in lines
        if not re.match(r"(?i)^here\s+(is|are)\b", line.strip())
    ]).strip()


def generate_use_cases(mini_scrape, services):
    prompt = f"""
Based on the company's services and the summary of their website below, list 4 to 6 practical use cases for explainer videos that could help the business communicate more clearly.

Each bullet must:
- Start with a gerund (e.g., Showing, Explaining, Clarifying, Walking through)
- Be short (under 20 words)
- Be clear, natural, and human — avoid jargon or corporate language
- Directly relate to the company's actual services

Do not mention the company name.
Do not include any labels, intros, or explanations — just return the raw list, separated by the "|" as a delimiter.

Services:
{services}

Mini Scrape:
{mini_scrape}
"""
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=500,
        )
        return postprocess_output(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"❌ Error generating use cases: {e}")
        return None


def fetch_records():
    all_records = []
    offset = 0
    limit = 100

    while True:
        url = f"{BASE_URL}/api/v1/db/data/{PROJECT_ID}/{TABLE_ID}?limit={limit}&offset={offset}"
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()
        batch = data.get("list", [])
        if not batch:
            break
        all_records.extend(batch)
        offset += limit

    return all_records


def update_use_case(record_id, text):
    url = f"{BASE_URL}/api/v1/db/data/{PROJECT_ID}/{TABLE_ID}/{record_id}"
    response = requests.patch(url, headers=HEADERS, json={"use_case": text})
    response.raise_for_status()


def main():
    print("🚀 Generating use cases (10 req/min throttle)...")
    records = fetch_records()
    updated = 0

    for record in records:
        mini_scrape = record.get("mini_scrape", "").strip()
        services = record.get("services", "").strip()
        existing_use_case = record.get("use_case", "").strip()

        if not mini_scrape or not services or existing_use_case:
            continue

        print(f"🔍 Processing: {record.get('company_name', '[no name]')}")
        result = generate_use_cases(mini_scrape, services)

        if result:
            update_use_case(record["id"], result)
            updated += 1
            print("✅ Use case field updated")
        else:
            print("⚠️ Skipped due to generation issue")

        time.sleep(6)  # Respect 10 requests/min

    print(f"\n🎯 Done. {updated} records updated.")


if __name__ == "__main__":
    main()
