import os
import re
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# Groq setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def postprocess_output(text):
    lines = text.splitlines()
    clean_lines = [
        line for line in lines
        if not re.match(r"(?i)^here\s+(is|are)\b", line.strip())
    ]
    return "\n".join(clean_lines).strip()


def generate_use_cases(mini_scrape, services):
    prompt = f"""
Based on the company's services and the summary of their website below, list 4 to 6 practical use cases for explainer videos that could help the business communicate more clearly.

Each bullet must:
- Start with a verb (e.g., Show, Explain, Clarify, Walk through)
- Be short (under 20 words)
- Be clear, natural, and human — avoid jargon or corporate language
- Directly relate to the company's actual services

Do not mention the company name.
Do not include any labels, intros, or explanations — just return the raw bullet list.

Services:
{services}

Mini Scrape:
{mini_scrape}
"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500,
        )
        raw_output = response.choices[0].message.content.strip()
        return postprocess_output(raw_output)
    except Exception as e:
        print(f"❌ Error generating use cases: {e}")
        return None


def main():
    print("🚀 Generating use cases...")
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        record_id = record.get("id")

        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        existing_use_case = fields.get("use case", "").strip()

        if not mini_scrape or not services or existing_use_case:
            continue

        print(f"🔍 Processing: {fields.get('company name', '[unknown company]')}")

        result = generate_use_cases(mini_scrape, services)

        if result:
            airtable.update(record_id, {"use case": result})
            updated_count += 1
            print("✅ Use case field updated")
        else:
            print("⚠️ Skipped due to generation issue")

    print(f"\n🎯 Done. {updated_count} records updated.")


if __name__ == "__main__":
    main()
