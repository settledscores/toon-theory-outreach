import os
import requests
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable config
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)


def generate_use_cases(mini_scrape, services):
    prompt = f"""
You're generating 3–6 specific, visual use cases for explainer videos tailored to this company’s services.

Avoid fluff or general HR slogans. Be concrete, useful, and visual. These are short video ideas — things the company might *show or explain* in 60–90 seconds to win trust or drive action.

Each use case should be:
- phrased like an actual video idea or benefit
- specific to the company's services or audience
- visual and practical, not abstract

Good examples:
- Showing potential clients how a Fractional Analyst actually helps
- Explaining the “One KPI” concept in 90 seconds
- Walking viewers through a dashboard’s value without a single spreadsheet
- Clarifying complex services (e.g., expat issues, startup structuring)
- Reinforcing your positioning as a trusted advisor
- Equipping your sales team with visual tools that close deals faster
- Reducing time spent repeating the same explanations

Bad examples (do not do this):
- "Transform HR with powerful strategies"
- "Drive engagement and passion through innovative storytelling"
- "Empower your brand with clarity and growth"

Use this context:

Mini scrape:
{mini_scrape}

Services:
{services}

Return only the final list. Bullet format. Do not explain yourself or label anything.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a B2B explainer video strategist."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 400,
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    print("🚀 Generating use cases...")
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        use_cases = fields.get("use cases", "").strip()

        if not mini_scrape or not services or use_cases:
            continue

        company = fields.get("company name", "[Unknown Company]")
        print(f"✏️ Creating use cases for: {company}")

        generated = generate_use_cases(mini_scrape, services)
        if generated:
            airtable.update(record["id"], {"use cases": generated})
            updated += 1
            print("✅ Updated use cases")
        else:
            print("⚠️ Skipped due to error")

    print(f"\n🎯 Done. {updated} records updated.")


if __name__ == "__main__":
    main()
