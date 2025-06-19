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


def generate_niche_summary(mini_scrape, services):
    prompt = f"""
You're writing a concise two-sentence summary of a company's focus and value proposition based on its website copy.

Mini scrape:
{mini_scrape}

Services:
{services}

Avoid repetition. Be clear, not clever. Just describe what they do and who they help.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are a precise summarizer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def main():
    print("🚀 Generating niche summaries...")
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        niche_summary = fields.get("niche summary", "").strip()

        if not mini_scrape or not services or niche_summary:
            continue

        name = fields.get("company name", "[unknown]")
        print(f"🔍 Processing: {name}")

        try:
            summary = generate_niche_summary(mini_scrape, services)
            airtable.update(record["id"], {"niche summary": summary})
            print(f"✅ Updated Airtable")
            updated_count += 1
        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated_count} records updated.")


if __name__ == "__main__":
    main()
