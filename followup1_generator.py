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

We create animated explainer videos that help businesses like {company} break down the dense copy and turn them into something clear and engaging.

I still think there’s potential to try this out with one of your core offerings. Such as {use_case_3} or {use_case_2}

I’d still be more than happy to draft a script or sketch a ten-second demo to show what kind of potential this could have. All at zero cost to you.

Either way, thanks again for all the work you’re putting out; it really makes a difference. 

{signature}
""",
    """Hi there {name},

Just wanted to follow up on my last note in case it got buried.

I genuinely think animated storytelling could help bring ideas like {use_case_1} or {use_case_2} into sharper focus for your audience.

We make the whole process simple: scripting, illustrations, storyboard, voiceover — all done for you. 

I’d be happy to draft a quick teaser at zero cost to you, just to show what it could look like in action. 

Let me know if you’re open to that. No pressure at all; just a genuine offer to collaborate.

{signature}
""",
    """Hi {name},

Hope your week’s going well so far.

I wanted to follow up on my last email about Toon Theory; the animation studio I run. We create whiteboard explainer videos that simplify complex ideas, especially for companies like {company} doing meaningful work.

If you’re still exploring ways to make things like {use_case_1} or {use_case_3} more engaging, I’d be happy to sketch a sample or share a quick storyboard. No charge. No pressure. Just a thoughtful way to explore the idea visually. 

Let me know if you’re curious. I’ll make it easy.

{signature}
""",
    """Hey {name},

I figured I’d follow up on my previous note from a couple days back just in case it got buried.

I mentioned how we create animated explainers to help businesses like {company} cut through the noise and supercharge their message. And I still think that {use_case_2} or {use_case_1} could work beautifully as a 90-second explainer. 

If you’re open to it, I can put together a brief teaser or script to show what that might look like, at zero cost to you, just something to get the ideas flowing.

Either way, thanks again for all the work you’re putting out; it really makes a difference. 

{signature}
""",
    """Hello {name}

Just wanted to follow up on my earlier note about using short explainer videos to showcase what {company} can do

I know you’re busy, so no pressure; but I’d still love to share a quick teaser tailored to one of your core offerings. Such as {use_case_2} or {use_case_3} 

Even a 10-second sketch can give you a feel for how whiteboard animation could simplify the way you communicate amongst teams or how you provide industry-specific insights to your clients.

Let me know if you’d be open to taking a look; no commitment at all, just a creative starting point.

{signature}
"""
]

def generate_email_2(fields):
    template = random.choice(TEMPLATES)
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
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        if "email 2" in fields and fields["email 2"].strip():
            continue

        if not all(k in fields for k in ["name", "company name", "inline 1", "inline 2", "inline 3", "signature"]):
            continue

        email_2_content = generate_email_2(fields)
        airtable.update(record["id"], {"email 2": email_2_content})
        print(f"✅ Updated email 2 for: {fields.get('name')}")
        updated += 1

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
