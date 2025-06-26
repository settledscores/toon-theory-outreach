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

def clean_use_cases(raw_text):
    raw = str(raw_text or "")
    raw_list = [item.strip() for item in raw.split("|") if item.strip()]
    cleaned = []
    for item in raw_list:
        item_clean = re.sub(r"[^\w\s]", "", item).lower()
        cleaned.append(item_clean)
        if len(cleaned) == 3:
            break
    return cleaned

def generate_followup_email(fields, template, use_cases):
    return template.format(
        name=fields.get("name", "[name]").strip(),
        company=fields.get("company name", "[company]").strip(),
        use_case_1=use_cases[0] if len(use_cases) > 0 else "[use case 1]",
        use_case_2=use_cases[1] if len(use_cases) > 1 else "[use case 2]",
        use_case_3=use_cases[2] if len(use_cases) > 2 else "[use case 3]",
        signature=fields.get("signature", "[signature]").strip()
    )

def main():
    records = airtable.get_all()
    updated = 0

    random.shuffle(TEMPLATES)

    for record in records:
        fields = record.get("fields", {})
        record_id = record["id"]

        if fields.get("email 2", "").strip():
            continue

        if "use case" in fields and "name" in fields and "company name" in fields and "signature" in fields:
            use_cases = clean_use_cases(fields["use case"])
            if len(use_cases) < 2:
                continue  # not enough clean use cases to generate email

            template = random.choice(TEMPLATES)
            email_content = generate_followup_email(fields, template, use_cases)
            airtable.update(record_id, {"email 2": email_content})
            updated += 1
            print(f"✅ Email 2 written for: {fields['name']}")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
