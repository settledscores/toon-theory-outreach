import os
import time
import random
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq
from difflib import SequenceMatcher

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
client = Groq(api_key=GROQ_API_KEY)

def extract_abbreviations(text):
    return set(word.strip() for word in text.split() if word.isupper() and len(word) >= 2)

def capitalize_abbreviations(summary, allowed_abbrs):
    words = summary.split()
    return " ".join(word.upper() if word.upper() in allowed_abbrs else word.lower() for word in words)

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio() > 0.4

def generate_summary(prompt):
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You write short, factual niche summaries (max 12 words). Use lowercase. No punctuation. Start with a present participle verb like helping, building, offering."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=50,
    )
    return response.choices[0].message.content.strip().lower()

def build_prompt(mini_scrape, services):
    return f"""
Generate a clear, value-focused summary of what a business does and for whom.

- Use lowercase only
- Max 12 words
- No punctuation
- Start with a present participle verb (e.g., helping, building, offering)
- Avoid fluff or generic terms
- Return only the phrase

Mini scrape:
{mini_scrape}

Services:
{services}
"""

def main():
    print("🚀 Generating summary paragraph 1...")
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        if fields.get("niche summary paragraph"):
            continue

        mini_scrape = fields.get("mini scrape", "")
        services = fields.get("services", "")
        if not mini_scrape or not services:
            continue

        abbrs = extract_abbreviations(mini_scrape + " " + services)
        prompt = build_prompt(mini_scrape, services)
        retries = 2

        for _ in range(retries):
            try:
                summary = generate_summary(prompt)
                summary = capitalize_abbreviations(summary, abbrs)
                airtable.update(record["id"], {"niche summary paragraph": summary})
                print(f"✅ Updated record: {summary}")
                updated += 1
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(random.uniform(2, 5))

        time.sleep(random.uniform(2.5, 3.5))  # Prevent 429s

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
