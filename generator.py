import os
import requests
from airtable import Airtable
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === Config ===
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = "llama3-70b-8192"

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)


def generate_email_with_variation(name, company, niche_summary, services, use_cases):
    # Trim field sizes
    niche_summary = niche_summary.strip()[:800]
    services = services.strip()[:800]
    use_case_lines = [
        uc.strip().lstrip("-•").rstrip(".")
        for uc in use_cases.splitlines()
        if uc.strip()
    ]

    use_case_1 = f"Use Case #1: {use_case_lines[0]}" if len(use_case_lines) > 0 else ""
    use_case_2 = f"Use Case #2: {use_case_lines[1]}" if len(use_case_lines) > 1 else ""
    use_case_3 = f"Use Case #3: {use_case_lines[2]}" if len(use_case_lines) > 2 else ""

    prompt = f"""
You're Trent, founder of Toon Theory. Write a short, warm cold email to {name} at {company} based only on the Airtable fields below.

Do not repeat anything. Do not make anything up. Keep it under 200 words, clear and helpful.

Niche Summary: {niche_summary}

Services: {services}

Use Cases:
{use_case_1}
{use_case_2}
{use_case_3}

Format:
- Begin with: Subject: A thought for your next project at {company}
- Greet them by name
- Refer naturally to the niche summary
- Describe Toon Theory clearly in one sentence
- Mention relevance to their services
- List only the 3 numbered use cases — do not alter them
- End with a grateful closer referencing their mission or tone
- Never use em dashes
- No commentary or labels — return only the email
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write clean, friendly, accurate cold emails. Only use the info provided. "
                    "Do not invent or repeat content. Format exactly as asked. Never use em dashes."
                )
            },
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error from Groq for {name}: {e}")
        print("🔍 Response content:", res.text if 'res' in locals() else "No response")
        return None


def main():
    print("🚀 Starting email generation...")
    records = airtable.get_all()
    generated_count = 0

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        niche_summary = fields.get("niche summary", "").strip()
        services = fields.get("services", "").strip()
        use_cases = fields.get("use cases", "").strip()

        if not name or not company or not niche_summary or not services or not use_cases:
            continue

        if "email 1" in fields:
            continue

        print(f"✏️ Generating for {name} ({company})...")

        email_text = generate_email_with_variation(name, company, niche_summary, services, use_cases)
        if email_text:
            airtable.update(record["id"], {
                "email 1": email_text,
                "initial date": datetime.utcnow().isoformat()
            })
            print(f"✅ Saved email for {name}")
            generated_count += 1
        else:
            print(f"⚠️ Skipped {name} due to generation error")

    print(f"\n🎯 Done. Emails generated: {generated_count}")


if __name__ == "__main__":
    main()
