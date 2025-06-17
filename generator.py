import os
import requests
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# === Airtable ===
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = os.environ['AIRTABLE_TABLE_NAME']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']

# === Groq ===
GROQ_API_KEY = os.environ['GROQ_API_KEY']
GROQ_MODEL = "mixtral-8x7b-32768"

# === Core Prompt Generator ===
def generate_email_with_template(name, company, web_copy):
    prompt = f"""You're helping a whiteboard animation studio write a cold outreach email.

Hi {name},

I’ve been following {company} lately, and your ability to make complex topics approachable really stood out.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your focus on clarity and communication, I think there’s real potential to add a layer of visual storytelling that helps even more people “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to:

- [Use case #1 tailored to website content]
- [Use case #2 tailored to website content]
- [Use case #3 tailored to website content]

If you're open to it, I’d love to draft a sample script or sketch out a short ten-second demo to demonstrate one of these use cases, all at no cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.

[Dynamic closer based on brand tone or mission. For example: “Thanks for making data feel human, it’s genuinely refreshing.” Or “Thanks for making healthcare more accessible, it's inspiring.”]

STRICT RULE: Do not use em dashes (—) under any circumstances. Replace them with commas, semicolons, or full stops. This is non-negotiable.

Website content:
{web_copy}
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant writing short, custom cold emails for a whiteboard animation studio. Avoid em dashes."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error from Groq for {name}: {e}")
        return None

# === Main Script ===
def main():
    print("🚀 Starting email generation...")
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()

    for record in records:
        fields = record.get("fields", {})
        record_id = record["id"]

        # Skip if already has email_1
        if "email_1" in fields and fields["email_1"].strip():
            continue

        # Check required fields
        if not all(key in fields and fields[key].strip() for key in ["name", "company name", "web copy"]):
            continue

        name = fields["name"]
        company = fields["company name"]
        web_copy = fields["web copy"]

        print(f"✏️ Generating for {name} ({company})...")

        email_text = generate_email_with_template(name, company, web_copy)
        if email_text:
            airtable.update(record_id, {"email_1": email_text})
            print(f"✅ Saved email for {name}")
        else:
            print(f"⚠️ Skipped {name} due to generation error")

    print("🔁 Finished processing all leads.")

if __name__ == "__main__":
    main()
