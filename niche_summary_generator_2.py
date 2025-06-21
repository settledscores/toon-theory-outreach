import os
import re
import time
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

ABBREVIATION_REGEX = re.compile(r"\b([A-Z]{2,5})\b", re.IGNORECASE)

def extract_abbreviations(text):
    """Extract uppercase abbreviations from text (like CPA, GTM, etc)."""
    return set(re.findall(r"\b[A-Z]{2,5}\b", text.upper()))

def generate_summary_prompt(mini_scrape, services):
    return f"""
You are writing a short, specific niche summary (max 12 words) that describes exactly what a company does and for whom.

✅ Rules:
- Start with a present participle verb (e.g. helping, building, streamlining)
- Use lowercase only **except** for abbreviations already present in the text (like CPA, GTM, M&A, etc)
- No punctuation
- Avoid generic fluff
- Be direct and descriptive
- Respond with only the phrase — no commentary or labels

Examples:
helping startups access clean no strings funding
streamlining hr processes for scaling businesses
supporting founders with tailored financial ops strategy

Mini scrape:
{mini_scrape}

Services:
{services}

Respond with a short phrase only. No punctuation.
"""

def lowercase_with_exceptions(text, exceptions):
    def preserve(match):
        word = match.group(0)
        return word if word.upper() in exceptions else word.lower()
    return re.sub(r'\b\w+\b', preserve, text)

def is_similar(summary1, summary2):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, summary1, summary2).ratio() > 0.4

def generate_niche_summary(mini_scrape, services, original_summary=None):
    prompt = generate_summary_prompt(mini_scrape, services)

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You generate ultra-brief, lowercase niche summaries with abbreviations preserved."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=30,
    )

    summary = response.choices[0].message.content.strip()
    exceptions = extract_abbreviations(mini_scrape + services)
    cleaned = lowercase_with_exceptions(summary, exceptions)

    if original_summary and is_similar(cleaned, original_summary):
        raise ValueError("Generated summary is too similar to the original")

    return cleaned

def main():
    print("🚀 Generating summary paragraph 2...")
    records = airtable.get_all()
    updated_count = 0
    delay = 60 / 25  # Limit to 25 requests per minute

    for record in records:
        fields = record.get("fields", {})
        record_id = record["id"]
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        summary1 = fields.get("niche summary paragraph", "").strip()
        summary2 = fields.get("niche summary paragraph 2", "").strip()

        if not mini_scrape or not services:
            continue

        try:
            summary = generate_niche_summary(mini_scrape, services, original_summary=summary1)
            airtable.update(record_id, {"niche summary paragraph 2": summary})
            print(f"✅ Updated record: {summary}")
            updated_count += 1
        except ValueError as ve:
            print(f"⚠️ Skipping duplicate-like summary: {ve}")
        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(delay)

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
