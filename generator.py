import os
import requests
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# === Constants ===
AIRTABLE_BASE_ID = os.environ['AIRTABLE_BASE_ID']
AIRTABLE_TABLE_NAME = os.environ['AIRTABLE_TABLE_NAME']
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
GROQ_API_KEY = os.environ['GROQ_API_KEY']

PROMPT_TEMPLATE = """You're helping a whiteboard animation studio write a cold outreach email.

Here is their base email:

Hi {name},

I’ve been following {company} lately, and your ability to make {summary} really stood out.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your focus on {angle}, I think there’s real potential to add a layer of visual storytelling that helps even more people “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to:

- [Use case #1 tailored to website content]
- [Use case #2 tailored to website content]
- [Use case #3 tailored to website content]

If you're open to it, I’d love to draft a sample script or sketch out a short ten-second demo to demonstrate one of these use cases, all at no cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.

[Dynamic closer based on brand tone or mission. For example: “Thanks for making data feel human, it’s genuinely refreshing.” Or “Thanks for making healthcare more accessible, it's inspiring.”]

Warm regards,  
Trent  
Founder, Toon Theory  
www.toontheory.com  
Whiteboard Animation For The Brands People Trust

STRICT RULE: Do not use em dashes (—) under any circumstances. Replace them with commas, semicolons, or full stops. This is non-negotiable.

Website content: {web_copy}
"""

def generate_with_groq(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": "mixtral-8x7b-32768"
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

def main():
    airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        if 'email 1' in fields and fields['email 1'].strip():
            continue  # Already has a generated email

        required = ['name', 'company name', 'web copy']
        if not all(k in fields and fields[k].strip() for k in required):
            continue

        try:
            prompt = PROMPT_TEMPLATE.format(
                name=fields['name'],
                company=fields['company name'],
                summary="complex topics approachable",
                angle="clarity and communication",
                web_copy=fields['web copy']
            )
            email = generate_with_groq(prompt)
            airtable.update(record['id'], {'email 1': email})
            updated += 1
            print(f"✅ Updated email 1 for {fields['name']}")

        except Exception as e:
            print(f"❌ Error processing {fields.get('name', 'unknown')}: {e}")

    print(f"🔁 Finished. Emails generated: {updated}")

if __name__ == '__main__':
    main()
