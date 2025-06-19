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


def first_sentence(text):
    return text.split(".")[0].strip() + "." if "." in text else text.strip()


def generate_email(name, company, mini_scrape, niche_summary, services, use_cases):
    short_niche = first_sentence(niche_summary)
    short_services = first_sentence(services)
    top_use_cases = [uc.strip("• ").strip() for uc in use_cases.strip().splitlines() if uc.strip()]
    top_use_cases = top_use_cases[:3]

    # Backup if use cases are fewer than 3
    while len(top_use_cases) < 3:
        top_use_cases.append("Explain a key aspect of your service clearly")

    prompt = f"""
You are Trent, founder of Toon Theory, writing a warm, conversational cold email to {name} at {company}. Follow the template exactly. The tone is natural and human, not salesy. No buzzwords. No filler. No em dashes. Structure is fixed. Just replace the brackets.

Template:
---
Subject: A thought for your next project at {company}

Hi {name},

I’ve been following {company} lately, {short_niche} and your ability to make data feel approachable, and even fun, for small businesses {short_niche} really struck a chord with me.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your strong emphasis on {short_services} making dashboards actionable and client-friendly, {short_services} I think there’s real potential to add a layer of visual storytelling that helps even more business owners “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to:

1. {top_use_cases[0]}
2. {top_use_cases[1]}
3. {top_use_cases[2]}

If you're open to it, I’d love to share a few tailored samples or sketch out what this could look like for {company}’s brand voice.

{short_niche} Thanks for making data feel human, it’s genuinely refreshing. {short_niche}

Warm regards,  
Trent  
Founder, Toon Theory  
www.toontheory.com  
Whiteboard Animation For The Brands People Trust
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that formats cold emails. Never invent. Never rephrase. Follow the template exactly."},
            {"role": "user", "content": prompt}
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
        niche_summary = fields.get("niche summary", "").strip()
        services = fields.get("services", "").strip()
        use_cases = fields.get("use cases", "").strip()

        if not all([name, company, mini_scrape, niche_summary, services, use_cases]):
            continue
        if "email 1" in fields:
            continue

        print(f"✏️ Generating for {name} ({company})...")
        email_text = generate_email(name, company, mini_scrape, niche_summary, services, use_cases)

        if email_text:
            airtable.update(record["id"], {
                "email 1": email_text,
                "initial date": datetime.utcnow().isoformat()
            })
            print(f"✅ Saved email for {name}")
            generated_count += 1
        else:
            print(f"⚠️ Skipped {name} due to generation error")

    print(f"\n🎯 Finished. Emails generated: {generated_count}")


if __name__ == "__main__":
    main()
