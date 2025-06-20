import os
from airtable import Airtable
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
airtable = Airtable(os.getenv("AIRTABLE_BASE_ID"), os.getenv("AIRTABLE_TABLE_NAME"), os.getenv("AIRTABLE_API_KEY"))
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_paragraphs(services):
    prompt = f"""
Generate 10 variations of this paragraph for a cold email. The paragraph should connect the company's services to the benefit of whiteboard animation.

These are the company’s services:
{services}

Each paragraph should:
- Be 2–3 sentences
- Refer to the services naturally (don't list them)
- Suggest how visual storytelling can help explain or amplify them
- Be written in friendly, clear, natural English

Avoid generic lines like "we can help you grow."

List exactly 10 variants.
"""

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": "You connect company services to explainer video benefits."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=800,
    )
    return response.choices[0].message.content.strip()

def main():
    for record in airtable.get_all():
        fields = record.get("fields", {})
        if "third paragraph variants" in fields:
            continue
        services = fields.get("services", "")
        if not services:
            continue

        print("📄 Generating third paragraph variants...")
        try:
            result = generate_paragraphs(services)
            airtable.update(record["id"], {"third paragraph variants": result})
            print("✅ Third paragraph variants saved")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
