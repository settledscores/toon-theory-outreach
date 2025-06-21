import os
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Airtable + Groq Setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
client = Groq(api_key=GROQ_API_KEY)

def generate_short_niche_summary(mini_scrape, services):
    prompt = f"""
You are writing a short, specific niche summary (max 12 words) that describes exactly what a company does and for whom.

✅ Requirements:
- Start with a present participle verb (e.g. helping, building, making, enabling, supporting, streamlining)
- Use lowercase only
- No punctuation
- Avoid fluff like "empowering businesses" or "delivering success"
- Be clear, not clever
- No preambles or labels — just return the phrase

Here are some examples:

helping startups access clean no strings funding  
making data approachable and even fun for small teams  
streamlining hr processes for scaling businesses  
providing saas engineers with expert data driven insights  
building logistics software for african retailers  
supporting founders with tailored financial ops strategy  

Now generate one like this based on the inputs below.

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
        temperature=0.3,
        max_tokens=30,
    )
    return response.choices[0].message.content.strip().lower()


def main():
    print("🚀 Generating two short niche summaries...")
    records = airtable.get_all()
    updated_count = 0

    for record in records:
        fields = record.get("fields", {})
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()
        summary_1 = fields.get("niche summary paragraph", "").strip()
        summary_2 = fields.get("niche summary paragraph 2", "").strip()

        # Skip if we don't have content or already populated summaries
        if not mini_scrape or not services or summary_1 or summary_2:
            continue

        print(f"🔍 Processing: {fields.get('company name', '[unknown]')}")

        try:
            first = generate_short_niche_summary(mini_scrape, services)
            second = generate_short_niche_summary(mini_scrape, services)

            if first == second:
                second += " "  # Slightly force uniqueness without breaking formatting

            airtable.update(record["id"], {
                "niche summary paragraph": first,
                "niche summary paragraph 2": second
            })

            print(f"✅ Summary 1: {first}")
            print(f"✅ Summary 2: {second}")
            updated_count += 1

        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🎯 Done. {updated_count} records updated.")


if __name__ == "__main__":
    main()
