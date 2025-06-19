import os
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
    return f"""
Here is text from a company’s website. Extract only the **core services or offerings** that the company provides. 
Do not include team bios, testimonials, values, blog content, or filler.

Only return a clean, readable list or summary of the actual services provided by the business. 
Do not include labels like “Here’s what I found” or explanations.

Text:
{text}
"""


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
                    {
                        "role": "system",
                        "content": (
                            "You extract only core services or offerings from business websites. "
                            "Do not return any commentary, metadata, or unnecessary formatting. "
                            "Only return a cleaned, readable list of services."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            services_output = response.choices[0].message.content.strip()
            update_services_field(record["id"], services_output)
            updated += 1
            print("✅ Services field updated")
        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated} records updated.")


if __name__ == "__main__":
    main()
