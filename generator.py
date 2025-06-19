import os
from airtable import Airtable
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# === Config ===
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"

airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)
client = Groq(api_key=GROQ_API_KEY)


def format_email(name, company, niche_summary, services, use_cases):
    # Ensure all fields are clean
    name = name.strip()
    company = company.strip()
    niche_summary = niche_summary.strip()
    services = services.strip()
    use_cases = [uc.strip().lstrip("-•") for uc in use_cases.splitlines() if uc.strip()]

    subject_lines = [
        f"Subject: Quick idea for {company}",
        f"Subject: A thought for your next project at {company}",
        f"Subject: Something that might help {company}",
        f"Subject: Curious if this could help {company}",
        f"Subject: Noticed something at {company}, had a thought",
    ]

    import random
    subject = random.choice(subject_lines)

    # Insert 3 clean use cases
    bullet_points = use_cases[:3]
    bullets = "\n".join([f"{point}," for point in bullet_points[:-1]])
    bullets += f"\nOr {bullet_points[-1]}..."

    # Compose final message
    email = f"""{subject}

Hi {name},

I’ve been following {company} lately, {niche_summary} and your ability to make data feel approachable, and even fun, for small businesses {niche_summary} really struck a chord with me.

I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.

With your strong emphasis on {services} I think there’s real potential to add a layer of visual storytelling that helps even more business owners “get it” faster.

Our animations are fully done-for-you (script, voiceover, storyboard, everything) and often used by folks like you to:

{bullets}

If you're open to it, I’d love to share a few tailored samples or sketch out what this could look like for {company}’s brand voice.

Thanks for making HR feel human — it’s genuinely refreshing.

Warm regards,  
Trent  
Founder, Toon Theory  
www.toontheory.com  
Whiteboard Animation For The Brands People Trust
"""
    return email.strip()


def main():
    print("🚀 Starting email generation...")
    records = airtable.get_all()
    generated_count = 0

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        niche = fields.get("niche summary", "").strip()
        services = fields.get("services", "").strip()
        use_cases = fields.get("use cases", "").strip()

        if not name or not company or not niche or not services or not use_cases:
            continue
        if "email 1" in fields:
            continue

        print(f"✏️ Generating for {name} ({company})...")

        try:
            email_text = format_email(name, company, niche, services, use_cases)
            airtable.update(record["id"], {
                "email 1": email_text,
                "initial date": datetime.utcnow().isoformat()
            })
            print(f"✅ Saved email for {name}")
            generated_count += 1
        except Exception as e:
            print(f"❌ Failed for {name}: {e}")

    print(f"\n🎯 Done. {generated_count} emails written.")


if __name__ == "__main__":
    main()
