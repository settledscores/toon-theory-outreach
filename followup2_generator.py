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

SALUTATIONS = [
    "Hi", "Hey", "Hello",
    "Hi there", "Hey there", "Hello there"
]

SIGNATURES = [
    "Warm regards,\nTrent ;  Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent ;  Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent ;  Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent ;  Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent ;  Founder, Toon Theory\nwww.toontheory.com"
]

TEMPLATES = [
    """{salutation} {name},

Just circling back in case the timing makes more sense now. I still believe whiteboard animation could simplify something {company} is working on; whether that’s a pitch, process, or product.

If you’d like to test the waters, I’m happy to sketch something out to show what it might look like.

You’ll find past examples linked in my signature.

{signature}""",

    """{salutation} {name},

Still happy to share a quick sketch or visual sample if it’s helpful. Many of our clients use animation to break down services, explain strategy, or walk users through a process.

If {company} has anything you’re trying to simplify, I’d love to help you explore it.

You’ll find past examples in the signature below.

{signature}""",

    """{salutation} {name},

Thought I’d check in one last time.

If you're still curious what an explainer might look like for {company}, I’d be glad to share something rough; a short sketch, or script to get the ball rolling.

You can find our work in the link below.

{signature}""",

    """{salutation} {name},

Wanted to quickly follow up before I wrap things on my end.

Whiteboard animation is often a good fit for simplifying messaging, especially when you're trying to break through noise or explain something fast.

Let me know if you'd like to test an idea visually.

{signature}""",

    """{salutation} {name},

Just reaching out again before I archive this thread. If now’s a better time to try animation, I’d love to put something together.

Even a 10-second sketch can be a useful way to explore what’s possible.

Reply anytime.

{signature}""",

    """{salutation} {name},

If you’re still considering new ways to share what {company} does, whiteboard storytelling could be a great tool.

I’d be happy to send over a short visual draft to get the ideas flowing.

No pressure; just a creative option to keep in mind.

{signature}""",

    """{salutation} {name},

Hope this isn’t too forward; I just really think there’s potential to show off what {company} does through animation.

If you'd like to see what that might look like, I’d be happy to sketch something out.

{signature}""",

    """{salutation} {name},

Circling back once more before I close the loop.

If there’s anything at {company} you’ve been meaning to simplify, an animation could help bring that to life.

Happy to draft something visual if you'd like to see what that might look like.

{signature}""",

    """{salutation} {name},

Reaching out one last time. If you're still exploring creative ways to explain what you do, this might be a great fit.

I’d be glad to put together a simple teaser or sketch if you're curious.

{signature}""",

    """{salutation} {name},

Sometimes even a 10-second sketch can make a big difference when explaining something new.

I’d be happy to share one if you're interested in exploring animation for {company}.

{signature}""",

    """{salutation} {name},

Hope your week’s going okay. I’m wrapping up some projects and wanted to reach out again before I close things out.

If you'd still like to explore using video to share what {company} does, I’d love to help.

{signature}""",

    """{salutation} {name},

A quick follow-up before I close out my list. If now’s not the right time, no worries at all.

But if you’re curious about how animation might help {company}, I’m still open to sharing a quick visual idea.

{signature}""",

    """{salutation} {name},

No pressure at all; just following up to say I’d still be happy to sketch something for {company} if you're curious.

It could help simplify something you already offer, or clarify a new direction.

{signature}""",

    """{salutation} {name},

Whiteboard explainers are great for making complex ideas stick. If that’s something you’ve been thinking about at {company}, I’d love to share a quick draft.

You’ll find our work in the link below if you want to browse examples.

{signature}""",

def build_email(template, name, company, salutation, signature):
    return template.format(name=name, company=company, salutation=salutation, signature=signature)

def main():
    print("🚀 Generating final follow-up emails (Email 3)...")
    records = airtable.get_all()
    eligible = []

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("name", "").strip()
        company = fields.get("company name", "").strip()
        email3 = fields.get("email 3", "").strip()
        record_id = record["id"]

        print(f"→ Checking {record_id}...")

        if name and company and not email3:
            eligible.append((record_id, name, company))
            print("   ✅ Eligible")
        else:
            print("   ❌ Skipping ;  missing name/company or email 3 already exists")

    if not eligible:
        print("⚠️ No eligible records found.")
        return

    random.shuffle(eligible)

    updated = 0
    for i, (record_id, name, company) in enumerate(eligible):
        template = random.choice(TEMPLATES)
        salutation = random.choice(SALUTATIONS)
        signature = random.choice(SIGNATURES)
        content = build_email(template, name, company, salutation, signature)
        airtable.update(record_id, {"email 3": content})
        updated += 1
        print(f"✅ Email 3 written for {name}")

    print(f"\n🎯 Done. {updated} final follow-ups sent.")

if __name__ == "__main__":
    main()
