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

def generate_short_niche_summary(mini_scrape, services):
    prompt = f"""
Generate a short summary (maximum 6 words) of what this company does. Avoid labels, prefaces, or fluff. No introductions, just the value.

Mini scrape:
{mini_scrape}

Services:
{services}

Respond with just the 6-word phrase. Nothing else.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You are a precise summarizer. Output only 6 words maximum."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=30,
    )
    return response.choices[0].message.content.strip()

def main():
    print("🚀 Generating short niche summaries...")
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        short_summary = fields.get("niche summary paragraph", "").strip()

        if not mini_scrape or not services or short_summary:
            continue

        name = fields.get("company name", "[unknown]")
        print(f"🔍 Processing: {name}")

        try:
            summary = generate_short_niche_summary(mini_scrape, services)
            airtable.update(record["id"], {"niche summary paragraph": summary})
            print(f"✅ Updated: {summary}")
            updated_count += 1
        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
