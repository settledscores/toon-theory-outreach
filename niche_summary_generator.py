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
You are writing a short, specific niche summary (no more than 12 words) describing what a company does.

Requirements:
- Start with a present participle (e.g. helping, building, making, enabling, streamlining, supporting)
- Use only lowercase
- No punctuation or filler phrases
- Focus on what the company **actually does** and **for whom**
- Avoid vague phrases like "empowering businesses" or "delivering success"
- No intros, labels, preambles, or explanations — just the phrase

Mini scrape:
{mini_scrape}

Services:
{services}

Respond with only the phrase, nothing else. No punctuation.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You generate ultra-brief, lowercase niche summaries using present participles only."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=30,
    )
    return response.choices[0].message.content.strip().lower()

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
