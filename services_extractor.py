import os
import re
import requests
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Baserow setup
BASEROW_API_KEY = os.getenv("BASEROW_API_KEY")
BASEROW_OUTREACH_TABLE = os.getenv("BASEROW_OUTREACH_TABLE")
BASE_URL = f"https://api.baserow.io/api/database/rows/table/{BASEROW_OUTREACH_TABLE}"
HEADERS = {
    "Authorization": f"Token {BASEROW_API_KEY}",
    "Content-Type": "application/json"
}

# Groq setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_INPUT_LENGTH = 14000

def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]

def generate_prompt(text):
    return f"""Extract only the actual services provided by the company from the text below.

- No explanations, summaries, or assistant language.
- No intros like “Here are...”, “This company offers...”, or “The core services include...”.
- No bullet headers or section titles.
- Just return the raw list of service lines, one per line, with no extra wording or formatting.

{text}
"""

def postprocess_output(text):
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        line = line.strip()
        if re.match(r"(?i)^(here\s+(is|are)|the\s+company|this\s+company|core\s+services|services\s+include|they\s+offer)", line):
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()

def fetch_records():
    res = requests.get(BASE_URL + "?user_field_names=true", headers=HEADERS)
    res.raise_for_status()
    return res.json()["results"]

def update_services_field(record_id, text):
    res = requests.patch(f"{BASE_URL}/{record_id}/", headers=HEADERS, json={"services": text})
    res.raise_for_status()

def main():
    print("🚀 Extracting core offerings...")
    records = fetch_records()
    updated = 0

    for record in records:
        full_text = record.get("web copy", "")
        services_text = record.get("services", "")
        website = record.get("website", "[no website]")

        if not full_text or services_text:
            continue

        print(f"🔍 Extracting services for: {website}")

        truncated = truncate_text(full_text)
        prompt = generate_prompt(truncated)

        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )

            raw_output = response.choices[0].message.content.strip()
            cleaned_output = postprocess_output(raw_output)

            update_services_field(record["id"], cleaned_output)
            print("✅ Services field updated")
            updated += 1

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
