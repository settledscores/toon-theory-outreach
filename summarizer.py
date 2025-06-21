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
    clean_lines = [line for line in lines if not re.match(r"(?i)^here\s+(is|are)\b", line.strip())]
    return "\n".join(clean_lines).strip()


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
