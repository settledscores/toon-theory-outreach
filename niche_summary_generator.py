import os
import time
import re
from difflib import SequenceMatcher
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

# Calculate similarity ratio
def similarity_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Find and preserve acronyms from original content
def preserve_custom_acronyms(text, context):
    tokens = set(re.findall(r"\b[A-Z]{2,}\b", context))
    for acronym in tokens:
        text = re.sub(rf"\b{acronym.lower()}\b", acronym, text)
    return text

# Generate one summary
def generate_short_niche_summary(mini_scrape, services):
    prompt = f"""
You are writing a short, specific niche summary (max 12 words) that describes exactly what a company does and for whom.

✅ Requirements:
- Start with a present participle verb (e.g. helping, building, making, enabling, supporting, streamlining)
- Use lowercase only except for acronyms already used in the text below (e.g. CPA, GTM)
- No punctuation
- Avoid fluff like "empowering businesses" or "delivering success"
- Be clear, not clever
- No preambles or labels — just return the phrase

Examples:

helping startups access clean no strings funding  
making data approachable and even fun for small teams  
streamlining hr processes for scaling businesses  
providing saas engineers with expert data driven insights  
building logistics software for african retailers  
supporting founders with tailored financial ops strategy  

Now generate one based on the inputs below.

Mini scrape:
{mini_scrape}

Services:
{services}

Respond with only the phrase. No punctuation, no comments.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You generate ultra-brief, lowercase niche summaries using present participles only. Preserve acronyms that appear in the original content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=30,
    )

    raw_summary = response.choices[0].message.content.strip()
    return preserve_custom_acronyms(raw_summary, mini_scrape + " " + services)

# Main script
def main():
    print("🚀 Generating niche summaries...")
    records = airtable.get_all()
    updated_count = 0
    request_interval = 60 / 25  # 25 requests per minute

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        name = fields.get("company name", "[unknown]")

        if not mini_scrape or not services:
            print(f"⚠️ Skipping {name}: Missing mini scrape or services")
            continue

        print(f"🔍 Processing: {name}")

        try:
            summary1 = generate_short_niche_summary(mini_scrape, services)
            time.sleep(request_interval)

            summary2 = ""
            attempts = 0
            while attempts < 5:
                summary2 = generate_short_niche_summary(mini_scrape, services)
                time.sleep(request_interval)
                ratio = similarity_ratio(summary1, summary2)
                if ratio < 0.4:
                    break
                print(f"⚠️ Similarity too high ({round(ratio*100)}%), retrying...")
                attempts += 1

            airtable.update(record["id"], {
                "niche summary paragraph": summary1,
                "niche summary paragraph 2": summary2
            })
            print(f"✅ {name} → 1: {summary1} | 2: {summary2}")
            updated_count += 1

        except Exception as e:
            print(f"❌ Error for {name}: {e}")

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()

