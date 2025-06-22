import os
import time
import re
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
client = Groq(api_key=GROQ_API_KEY)

REQUESTS_PER_MINUTE = 20
SECONDS_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE

def generate_summary(mini_scrape, services):
    prompt = f"""
You are an API that returns a short, lowercase business-focused phrase with no punctuation.
It must:
- Start with a present participle verb (e.g., empowering, guiding, streamlining)
- Be max 12 words
- Be grounded in real services — not vague goals or inspiration
- Avoid second-person pronouns (no "you", "your", "yours")
- Avoid hype or motivational words like "brilliant", "heroes", or "success"
- Pull wording directly from the mini scrape and services
- Return only one phrase. No intros, no formatting, no extra text.

Examples of strong phrasing:
- empowering businesses to streamline their hr processes
- guiding startups through capital raising
- streamlining payment processing with custom automation tools
- building customized financial projection models
- delivering tailored recruitment solutions
- providing comprehensive financial services to small businesses

Mini scrape:
{mini_scrape}

Services:
{services}
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "Return one lowercase phrase with no punctuation. No prefix, no formatting."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=30,
    )
    return response.choices[0].message.content.strip().lower()

def main():
    print("🚀 Generating summary paragraph 1...")
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        summary = fields.get("niche summary paragraph", "").strip()

        if not mini_scrape or not services or summary:
            continue

        try:
            result = generate_summary(mini_scrape, services)
            airtable.update(record["id"], {"niche summary paragraph": result})
            print(f"✅ Updated record: {result}")
            updated_count += 1
        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(SECONDS_BETWEEN_REQUESTS)

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
