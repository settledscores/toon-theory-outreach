import os
import requests
from airtable import Airtable
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === Config ===
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = "llama3-70b-8192"

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# === Follow-Up Generator ===
def generate_followup_email(name, company, web_copy):
    web_copy = web_copy.strip()[:1000]

        prompt = f"""
You are Trent, founder of Toon Theory, a whiteboard animation studio. You're writing a **first follow-up cold email** to {name} at {company}. This follow-up comes **3 days after** the initial message.

Your goal is to:
- Check in naturally without sounding scripted
- Briefly reference the earlier message without repeating it
- Show how Toon Theory could specifically help based on their site
- Offer a no-pressure, no-cost sample or 10s teaser
- Close warmly and with a nod to their mission, tone, or values

INSTRUCTIONS:
- DO NOT include any explanation, commentary, or labels in your output.
- DO NOT use em dashes under any circumstances. Use semicolons, commas, or periods instead. This is non-negotiable.
- DO NOT repeat body structures. Vary sentence order, phrasing, and tone naturally.
- Rotate **subject lines** on every output. Pick one randomly from this list:

Subject: Just checking in, {name}  
Subject: Wondering if this idea stuck with you  
Subject: Circling back on this  
Subject: Thought I’d follow up, {name}  
Subject: Still thinking about {company}  

Your message should sound like a real person thoughtfully following up — warm, brief, conversational. Not robotic, not fluffy. Flesch score above 80.

Use this **as inspiration**, not as a fixed template:

---
Subject: Thought I’d follow up, {name}

Hi {name},

Hope your week’s going well. Just wanted to follow up on the note I sent a few days ago about Toon Theory.

We create animated explainer videos that help companies like {company} break down complex messages and turn them into something clear and engaging.

I still think there’s potential to try this out with one of your core offerings. I’d still be more than happy to draft a short sample or sketch a no-cost ten-second demo to show what kind of potential this could have.

Either way, thanks for doing what you do best. Hope to hear from you soon.

Warm regards,  
Trent  
Founder, Toon Theory  
www.toontheory.com  
Whiteboard Animation For The Brands People Trust
---

Here’s their website context (use it to personalize use cases and tone):  
{web_copy}

Only return the complete message — subject line on top, followed by the email body. Do not include labels or descriptions.
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
                "content": "You are a helpful assistant that writes short, natural cold follow-up emails. Avoid em dashes at all times. Rotate subject lines and phrasing every time."
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
        print("🔍 Response content:", res.text if 'res' in locals() else "No response")
        return None

# === Main Script ===
def main():
    print("📨 Starting follow-up 1 generation...")
    records = airtable.get_all()
    generated_count = 0

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        web_copy = fields.get("web copy", "").strip()

        if not name or not company or not web_copy:
            continue

        # Skip if email 2 already exists
        if "email 2" in fields:
            continue

        print(f"✏️ Generating follow-up for {name} at {company}...")

        email_text = generate_followup_email(name, company, web_copy)
        if email_text:
            airtable.update(record["id"], {
                "email 2": email_text,
                "follow-up 1 date": datetime.utcnow().isoformat()
            })
            print(f"✅ Saved follow-up 1 for {name}")
            generated_count += 1
        else:
            print(f"⚠️ Skipped {name} due to generation error")

    print(f"🔁 Finished follow-up 1 generation. Total created: {generated_count}")

if __name__ == "__main__":
    main()
