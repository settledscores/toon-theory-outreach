import os
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
airtable = Airtable(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_TABLE_NAME"), os.getenv("AIRTABLE_API_KEY"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_subjects(company_name):
    prompt = f"""
Generate 10 unique, casual, and non-spammy subject lines for a cold outreach email to a company named "{company_name}".

- Subjects should feel conversational and relevant to business/creative services.
- Avoid emojis, all-caps, and aggressive sales language.
- Keep them short and interesting (max ~8 words each).
- List exactly 10 bullets.

Example styles:
- Wondering if this could help
- A quick idea for {company name}
- Making dashboards clearer (with video?)

Only return the subject lines.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You write short, natural subject lines for cold email outreach."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.85,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

def main():
    for record in airtable.get_all():
        fields = record.get("fields", {})
        if "subject variants" in fields:
            continue
        company_name = fields.get("company name", "")
        if not company_name:
            continue

        print(f"🧠 Generating subject variants for: {company_name}")
        try:
            subjects = generate_subjects(company_name)
            airtable.update(record["id"], {"subject variants": subjects})
            print("✅ Subject variants saved")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
