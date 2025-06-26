import os
import random
import re
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

# Airtable setup
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

TEMPLATES = [
    """Hey there {name},

Hope your week’s going well. Just wanted to follow up on the note I sent a few days ago about Toon Theory.

I still think there’s potential to try out animated storytelling with one of your core offerings. Such as {use_case_3} or {use_case_2}

I’d still be more than happy to draft a script or sketch a ten-second demo to show what kind of potential this could have. All at zero cost to you.

Feel free to reply this email if you're still curious to explore the fit — and there’s a link to our site in my signature if you’d like to check out some of our past work.

{signature}
""",
    """Hi {name},

Just wanted to follow up on my last note in case it got buried.

I genuinely think animated storytelling could help bring ideas like {use_case_1} or {use_case_2} into sharper focus for your audience.

We make the whole process simple: scripting, illustrations, storyboard, voiceover... all done for you. I’d be happy to draft a quick teaser of a sample script at no cost, just to show what it could look like in action. 

If that sounds worth exploring, feel free to reply. Our website’s link in my signature if you'd like to take a peek at some of our past projects.

{signature}
""",
    """Hi {name},

Hope your week’s going well so far.

I wanted to follow up on my last email about Toon Theory; the animation studio I run. Animated videos could simplify complex ideas, especially for businesses like {company} doing meaningful work.

If you’re still exploring ways to make things like {use_case_1} or {use_case_3} more engaging, I’d be happy to sketch a sample or share a quick storyboard. No charge. No pressure. Just a thoughtful way to explore the idea. 

Feel free to reply if you’re curious. Our website’s link is in my signature if you want to see check out some of our past projects.

{signature}
""",
    """Hi {name},

I figured I’d follow up on my previous note from a couple days back just in case it got buried.

I mentioned how we create animated explainers to help businesses like {company} cut through the noise and supercharge their messaging. And I still think: {use_case_2} or {use_case_1} could work beautifully as a 90-second explainer. 

If you’re open to it, I can put together a brief teaser or script to show what that might look like, at zero cost to you; just something to get the ideas flowing.

Let me know if this sounds like something worth trying. You’ll also find our website link in my signature if you'd like to take a peek at some of our past work.

{signature}
""",
    """Hi {name}

Just wanted to follow up on my earlier note about using short explainer videos to showcase what {company} can do

I know you’re busy, so no pressure; but I’d still love to share a quick teaser tailored to one of your core offerings. Such as {use_case_2} or {use_case_3} 

Even a 10-second sketch can give you a feel for how whiteboard animation could simplify the way you communicate among teams or how you provide industry-specific insights to your clients.

Feel free to reply if this could be worth a shot. You’ll also find a link to our website in my signature if you'd like to check out some of our previous projects.

{signature}
"""
]

SIGNATURES = [
    "Warm regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent — Founder, Toon Theory\nwww.toontheory.com"
]

def parse_use_cases(use_case_field):
    raw = str(use_case_field or "")
    return [re.sub(r'[^\w\s]', '', uc).lower().strip() for uc in raw.split("|") if uc.strip()][:3]

def generate_followup_email(fields, template, use_cases, signature):
    return template.format(
        name=fields.get("name", "[name]").strip(),
        company=fields.get("company name", "[company]").strip(),
        use_case_1=use_cases[0],
        use_case_2=use_cases[1],
        use_case_3=use_cases[2],
        signature=signature
    )

def main():
    print("🔍 Scanning records...")
    records = airtable.get_all()
    updated = 0

    for record in records:
        record_id = record["id"]
        fields = record.get("fields", {})

        print(f"→ Checking record {record_id} for update eligibility")

        name = fields.get("name")
        company = fields.get("company name")
        email_2 = fields.get("email 2", "")
        use_case_raw = fields.get("use case", "")

        if not name or not company:
            print("   Skipping — missing name or company.\n")
            continue
        if email_2.strip():
            print("   Skipping — email 2 already exists.\n")
            continue

        use_cases = parse_use_cases(use_case_raw)
        if len(use_cases) < 3:
            print(f"   Skipping — only found {len(use_cases)} use cases.\n")
            continue

        template = random.choice(TEMPLATES)
        signature = random.choice(SIGNATURES)
        content = generate_followup_email(fields, template, use_cases, signature)

        airtable.update(record_id, {"email 2": content})
        updated += 1
        print(f"✅ Email 2 updated for: {name}\n")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
