import os
import random
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

I mentioned how we create animated explainers to help businesses like {company} cut through the noise and supercharge their messaging. And I still that: {use_case_2} or {use_case_1} could work beautifully as a 90-second explainer. 

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

def generate_followup_1_email(fields, template):
    return template.format(
        name=fields.get("name", "[name]").strip(),
        company=fields.get("company name", "[company]").strip(),
        use_case_1=fields.get("inline 1", "[use case 1]").strip(),
        use_case_2=fields.get("inline 2", "[use case 2]").strip(),
        use_case_3=fields.get("inline 3", "[use case 3]").strip(),
        signature=fields.get("signature", "[signature]").strip()
    )

def main():
    records = airtable.get_all()
    eligible = []

    for record in records:
        fields = record.get("fields", {})
        if "email 2" not in fields or not fields["email 2"].strip():
            if all(k in fields for k in ["name", "company name", "inline 1", "inline 2", "inline 3", "signature"]):
                eligible.append((record["id"], fields))

    random.shuffle(eligible)
    random.shuffle(TEMPLATES)

    updated = 0
    for idx, (record_id, fields) in enumerate(eligible):
        template = TEMPLATES[idx % len(TEMPLATES)]
        content = generate_followup_1_email(fields, template)
        airtable.update(record_id, {"email 2": content})
        updated += 1
        print(f"✅ Email 2 updated for: {fields.get('name')}")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
