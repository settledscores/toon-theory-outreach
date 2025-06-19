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

SUBJECT_LINES = [
    "Subject: Quick idea for {company}",
    "Subject: A thought for your next project at {company}",
    "Subject: Something that might help {company}",
    "Subject: Curious if this could help {company}",
    "Subject: Noticed something at {company}, had a thought"
]

def format_use_cases(use_case_text):
    lines = [line.strip("•- ").strip().rstrip(",.") for line in use_case_text.strip().splitlines() if line.strip()]
    if not lines:
        return ""
    joined = (
        f"Showing {lines[0].lower()},\n"
        + (f"Explaining {lines[1].lower()},\n" if len(lines) > 1 else "")
        + (f"Or {lines[2][0].lower() + lines[2][1:]}..." if len(lines) > 2 else "")
    )
    return joined

def generate_email(name, company, mini_scrape, niche_summary, use_cases, services):
    subject = random_subject(company)
    use_case_block = format_use_cases(use_cases)
    closer_line = f"{niche_summary.strip() or services.strip()} Thanks for making data feel human, it’s genuinely refreshing."

    body = f"""
{subject}

Hi {name},

I’ve been following {company} lately, {niche_summary} and your ability to make data feel approachable, and even fun, for small businesses {niche_summary} really struck a chord with me.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your strong emphasis on {services} making dashboards actionable and client-friendly, {services} I think there’s real potential to add a layer of visual storytelling that helps even more business owners “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to:

{use_case_block}

If you're open to it, I’d love to share a few tailored samples or sketch out what this could look like for {company}’s brand voice.

{closer_line}

Warm regards,  
Trent  
Founder, Toon Theory  
www.toontheory.com  
Whiteboard Animation For The Brands People Trust
"""
    return body.strip()

def random_subject(company):
    import random
    return random.choice(SUBJECT_LINES).format(company=company)

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
        use_cases = fields.get("use cases", "").strip()
        services = fields.get("services", "").strip()

        if not all([name, company, mini_scrape, niche_summary, use_cases, services]):
            continue
        if "email 1" in fields:
            continue

        print(f"✏️ Generating for {name} ({company})...")

        email_text = generate_email(name, company, mini_scrape, niche_summary, use_cases, services)
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
