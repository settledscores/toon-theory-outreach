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


def generate_email_with_variation(name, company, mini_scrape, services):
    mini_scrape = mini_scrape.strip()[:1200]
    services = services.strip()[:800]

    prompt = f"""
You are Trent, the founder of Toon Theory, a whiteboard animation studio. You're writing a warm, conversational cold email to {name} at {company}, using the context below. The tone should be clear, human, and helpful — not salesy. No buzzwords. No filler. No em dashes.

Rotate both the subject line and body structure on every email you write. Use clean punctuation. Keep it short, natural, and easy to read.

Randomly choose one subject line and place it as the first line of the message:
- Subject: Quick idea for {company}
- Subject: A thought for your next project at {company}
- Subject: Something that might help {company}
- Subject: Curious if this could help {company}
- Subject: Noticed something at {company}, had a thought

---
Hi {name},

I’ve been following {company} lately, and your ability to make complex topics approachable really stood out.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your focus on clarity and communication, I think there’s real potential to add a layer of visual storytelling that helps even more people “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to:
- [Use case #1 tailored to the services]
- [Use case #2 tailored to the services]
- [Use case #3 tailored to the services]

If you're open to it, I’d love to draft a sample script or sketch out a short ten-second demo to demonstrate one of these use cases, all at no cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.

[Dynamic closer based on brand tone or mission. For example: “Thanks for making data feel human, it’s genuinely refreshing.” Or “Thanks for making healthcare more accessible, it's inspiring.”]
---

Website summary:
{mini_scrape}

Their services:
{services}

Return only the complete message — subject line first, then body. Do not include commentary. Do not label anything. Do not explain your choices. Do not mention that the list came from the services section. Use the service info to fill in the use cases. No em dashes allowed — ever. Use commas, periods, or semicolons instead.
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
                "content": "You are a helpful assistant that writes cold emails. Always vary structure. Never use em dashes."
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


def main():
    print("🚀 Starting email generation...")
    records = airtable.get_all()
    generated_count = 0

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        mini_scrape = fields.get("mini scrape", "").strip()
        services = fields.get("services", "").strip()

        if not name or not company or not mini_scrape or not services or "email 1" in fields:
            continue

        print(f"✏️ Generating for {name} ({company})...")

        email_text = generate_email_with_variation(name, company, mini_scrape, services)
        if email_text:
            airtable.update(record["id"], {
                "email 1": email_text,
                "initial date": datetime.utcnow().isoformat()
            })
            print(f"✅ Saved email for {name}")
            generated_count += 1
        else:
            print(f"⚠️ Skipped {name} due to generation error")

    print(f"🔁 Finished processing. Emails generated: {generated_count}")


if __name__ == "__main__":
    main()
