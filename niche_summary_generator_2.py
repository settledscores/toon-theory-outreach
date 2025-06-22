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

def is_bad_summary(text):
    if not text:
        return True
    if len(text.split()) < 4:
        return True
    if re.search(r"\byou(r)?\b", text.lower()):
        return True
    if not re.match(r"^(empowering|guiding|unlocking|delivering|streamlining|providing|developing|enhancing|connecting|facilitating|transforming|simplifying|managing|routing|pairing)\b", text.lower()):
        return True
    return False

def generate_replacement(mini_scrape, services):
    prompt = f"""
You are an API that returns a short, lowercase business-focused phrase with no punctuation.
It must:
- Start with a present participle verb (e.g., empowering, unlocking, transforming)
- Be max 12 words
- Avoid second-person pronouns ("you", "your", etc)
- Avoid vague or poetic phrases
- Be concrete, relevant, and pulled from the content below
- Return only one phrase. No intro, formatting, or extras.

Examples:
- empowering small business owners with personalized guidance
- guiding businesses through international tax compliance
- providing intelligent solutions for commercial real estate needs

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
        temperature=0.85,
        max_tokens=30,
    )
    return response.choices[0].message.content.strip().lower()

def main():
    print("🔎 Scanning for weak or off-tone summaries...")
    records = airtable.get_all()
    cleaned = 0

    for record in records:
        fields = record.get("fields", {})
        summary = fields.get("niche summary paragraph 2", "").strip()
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()

        if not is_bad_summary(summary):
            continue  # looks good, skip

        if not mini_scrape or not services:
            continue  # not enough context to rewrite

        try:
            new_summary = generate_replacement(mini_scrape, services)
            airtable.update(record["id"], {"niche summary paragraph 2": new_summary})
            print(f"✅ Rewritten: {summary} → {new_summary}")
            cleaned += 1
        except Exception as e:
            print(f"❌ Error on record {record.get('id')}: {e}")

        time.sleep(SECONDS_BETWEEN_REQUESTS)

    print(f"\n🎯 Cleanup done. {cleaned} summaries repaired.")

if __name__ == "__main__":
    main()
