import os
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
airtable = Airtable(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_TABLE_NAME"), os.getenv("AIRTABLE_API_KEY"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_openers(company_name, niche_summary):
    prompt = f"""
Generate 10 natural-sounding first-paragraph openers for a cold email to a company named "{company_name}". Use this short summary of what they do:

{niche_summary}

Each opener should:
- Mention the company name or refer to what they do
- Feel human and warm, not templated
- Be short (1–2 sentences)
- Avoid buzzwords and AI clichés

List exactly 10 bullets.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You write personalized, human cold email openers."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.85,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

def main():
    for record in airtable.get_all():
        fields = record.get("fields", {})
        if "opener variants" in fields:
            continue
        company_name = fields.get("company name", "")
        niche_summary = fields.get("niche summary", "")
        if not company_name or not niche_summary:
            continue

        print(f"💬 Generating openers for: {company_name}")
        try:
            result = generate_openers(company_name, niche_summary)
            airtable.update(record["id"], {"opener variants": result})
            print("✅ Opener variants saved")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
