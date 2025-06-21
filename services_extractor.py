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

MAX_INPUT_LENGTH = 14000


def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]


def generate_prompt(text):
    return f"""From the following text, extract only the core services or offerings provided by the company.

- Do not include team bios, values, testimonials, blogs, or generic claims.
- Do not return any explanations, intros, labels, or bullet list headers.
- Return only a clean, readable list of real services the business provides.

{text}
"""


def postprocess_output(text):
    lines = text.splitlines()
    clean_lines = [line for line in lines if not re.match(r"(?i)^here\s+(is|are)\b", line.strip())]
    return "\n".join(clean_lines).strip()


def update_services_field(record_id, text):
    airtable.update(record_id, {"services": text})


def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        full_text = fields.get("web copy", "")
        services_text = fields.get("services", "")

        if not full_text or services_text:
            continue

        print(f"🔍 Extracting services for: {fields.get('website', '[no website]')}")

        truncated = truncate_text(full_text)
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

            raw_output = response.choices[0].message.content.strip()
            cleaned_output = postprocess_output(raw_output)
            update_services_field(record["id"], cleaned_output)
            updated += 1
            print("✅ Services field updated")

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated} records updated.")


if __name__ == "__main__":
    main()
