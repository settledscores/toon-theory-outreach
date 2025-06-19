import os
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
client = Groq(api_key=GROQ_API_KEY)


def generate_use_cases(mini_scrape, services):
    prompt = f"""
Based on the content below, generate a list of 3–5 clear, specific use cases for animated explainer videos tailored to this company's services and messaging.

Each use case should be practical and phrased like a benefit. Use bullets. Do not label the list or explain anything.

Mini scrape:
{mini_scrape}

Services:
{services}
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You write clear use cases for animation, always formatted as a short bullet list."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def main():
    print("🚀 Generating use cases...")
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        use_cases = fields.get("use cases", "").strip()

        if not mini_scrape or not services or use_cases:
            continue

        name = fields.get("company name", "[unknown]")
        print(f"🔍 Processing: {name}")

        try:
            cases = generate_use_cases(mini_scrape, services)
            airtable.update(record["id"], {"use cases": cases})
            print(f"✅ Updated Airtable")
            updated_count += 1
        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated_count} records updated.")


if __name__ == "__main__":
    main()
