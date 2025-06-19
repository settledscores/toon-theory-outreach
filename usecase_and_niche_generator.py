import os
import re
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


def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate_text(text, limit=MAX_INPUT_LENGTH):
    return text[:limit]


def build_prompt(mini_scrape, services):
    return f"""
You are a helpful assistant extracting insight from business websites.

Based on the information below, do two things:

1. Create 3–5 highly specific **bulleted use cases** for whiteboard animation. Tailor them to the business’s services. Each bullet should sound realistic and natural, like something they’d actually do. Example bullets:

- Explain your services in a more human, less “tech-speak” way  
- Walk viewers through your dashboard’s value without a spreadsheet  
- Share founder stories, processes, or impact highlights visually

2. Then write a single short sentence that summarizes what this business does and for whom. This is the **niche summary**. Example:  
“Data consulting for small business owners.”  
“Fractional HR for growing startups.”  
“Legal support for early-stage African founders.”

Keep everything in plain English. Do not list your reasoning or label sections. Just return the bullet list, then the one-line summary.

Website summary:
{mini_scrape}

Their services:
{services}
"""


def update_fields(record_id, use_cases, niche_summary):
    airtable.update(record_id, {
        "use cases": use_cases.strip(),
        "niche summary": niche_summary.strip()
    })


def main():
    print("🚀 Generating use cases and niche summaries...")
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        use_cases = fields.get("use cases", "").strip()
        niche_summary = fields.get("niche summary", "").strip()

        if not mini_scrape or not services or (use_cases and niche_summary):
            continue

        print(f"🔍 Processing: {fields.get('company name', '[no name]')}")

        prompt = build_prompt(truncate_text(mini_scrape), truncate_text(services))

        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You extract tailored insights from business content."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            output = response.choices[0].message.content.strip()
            *use_lines, summary = output.strip().split("\n")
            bullet_text = "\n".join(line for line in use_lines if line.startswith("-"))

            update_fields(record["id"], bullet_text, summary)
            print("✅ Updated Airtable")
            updated += 1
        except Exception as e:
            print(f"❌ Error for {fields.get('company name', '[unknown]')}: {e}")

    print(f"\n🎯 Done. {updated} records updated.")


if __name__ == "__main__":
    main()
