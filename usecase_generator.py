import os
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

def generate_use_cases(mini_scrape, services):
    prompt = f"""
You're Trent, the founder of Toon Theory, a whiteboard animation studio. Based on the company's services and website summary below, list 4 to 6 practical use cases for explainer videos that could help this business communicate more clearly.

The use cases should:
- Be bulleted
- Each one should begin with a verb: Show, Explain, Highlight, Walk through, Clarify, etc.
- Be written in clear, conversational English — aim for a Flesch Reading Ease score of 80 or above
- Be short, scannable, and not verbose (no more than 20 words per bullet)
- Sound natural and informal; avoid corporate language or abstract phrasing
- Be directly relevant to the company’s actual services

Do not mention the company name. Just list use cases as if you're describing how explainer videos could help.

Services:
{services}

Mini Scrape:
{mini_scrape}

List the bullets below. Return only the use cases and nothing else.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You write short, clear, human-friendly marketing bullets. Always start each point with a verb."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error generating use cases: {e}")
        return None

def main():
    print("🚀 Generating use cases...")
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        record_id = record.get("id")

        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        use_cases = fields.get("use cases", "").strip()

        if not mini_scrape or not services or use_cases:
            continue

        print(f"🔍 Processing: {fields.get('company name', '[unknown company]')}")

        result = generate_use_cases(mini_scrape, services)

        if result:
            airtable.update(record_id, {"use cases": result})
            updated_count += 1
            print("✅ Updated Airtable")
        else:
            print("⚠️ Skipped due to generation issue")

    print(f"\n🎯 Done. {updated_count} records updated.")

if __name__ == "__main__":
    main()
