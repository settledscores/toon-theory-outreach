import os
import random
import re
from airtable import Airtable
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === Config ===
AIRTABLE_BASE_ID = os.environ["AIRTABLE_BASE_ID"]
AIRTABLE_TABLE_NAME = os.environ["AIRTABLE_TABLE_NAME"]
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

SUBJECT_LINES = [
    "Subject: Quick idea for {company}",
    "Subject: A thought for your next project at {company}",
    "Subject: Something that might help {company}",
    "Subject: Curious if this could help {company}",
    "Subject: Noticed something at {company}, had a thought"
]

def clean_niche_summary(text):
    lines = text.strip().splitlines()
    filtered = [
        line.strip()
        for line in lines
        if line and not re.match(r"(?i)^(about|our|the way|say hello|providers|from strategic|empowering|hr solutions)", line.strip())
    ]
    # Use the first paragraph with 20+ words
    for line in filtered:
        if len(line.split()) >= 20:
            return line.strip()
    return filtered[0] if filtered else ""

def format_services(text):
    items = [
        line.strip("•*- ").strip().rstrip(",.")
        for line in text.strip().splitlines()
        if line.strip() and not line.lower().startswith(("here is", "this is", "our services", "examples include"))
    ]
    if len(items) == 0:
        return ""
    elif len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]

def format_use_cases(text):
    lines = [
        line.strip("•*- ").strip().rstrip(",.")
        for line in text.strip().splitlines()
        if line.strip() and not line.lower().startswith(("here are", "use cases", "examples include"))
    ]
    if not lines:
        return ""
    joined = (
        f"Showing how {lines[0].lower()},\n"
        + (f"Explaining {lines[1].lower()},\n" if len(lines) > 1 else "")
        + (f"Or walking someone through {lines[2].lower()}..." if len(lines) > 2 else "")
    )
    return joined

def generate_email(name, company, mini_scrape, niche_summary, use_cases, services):
    subject = random.choice(SUBJECT_LINES).format(company=company)
    use_case_block = format_use_cases(use_cases)
    closer_line = "Thanks for making HR feel human — it’s genuinely refreshing."

    body = f"""
{subject}

Hi {name},

I’ve been following {company} lately, and your ability to make data feel approachable, and even fun, for small businesses really struck a chord with me. {niche_summary}

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your strong emphasis on {services}, I think there’s real potential to add a layer of visual storytelling that helps even more business owners “get it” faster.

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

def main():
    print("🚀 Starting email generation...")
    records = airtable.get_all()
    generated_count = 0

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        mini_scrape = fields.get("mini scrape", "").strip()
        niche_summary = clean_niche_summary(fields.get("niche summary", ""))
        use_cases = fields.get("use cases", "")
        services = format_services(fields.get("services", ""))

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
