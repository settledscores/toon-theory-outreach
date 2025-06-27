import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

# NocoDB config
NOCODB_API_KEY = os.getenv("NOCODB_API_KEY")
NOCODB_PROJECT_ID = os.getenv("NOCODB_PROJECT_ID")
NOCODB_OUTREACH_TABLE_ID = os.getenv("NOCODB_OUTREACH_TABLE_ID")
NOCODB_BASE_URL = os.getenv("NOCODB_BASE_URL")
API_BASE = f"{NOCODB_BASE_URL}/v1/db/data"
HEADERS = {
    "Authorization": f"Bearer {NOCODB_API_KEY}",
    "Content-Type": "application/json"
}

SALUTATIONS = [
    "Hi", "Hey", "Hello", "Hi there", "Hey there", "Hello there"
]

SIGNATURES = [
    "Warm regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent — Founder, Toon Theory\nwww.toontheory.com"
]

TEMPLATES = [
    """{salutation} {name},

Just circling back in case the timing makes more sense now. I still believe whiteboard animation could amplify something {company} is working on, whether that is a pitch, process, or product.

If you would like to test the waters, I am happy to sketch something out to show what it might look like.

You will find past examples linked in my signature. Feel free to reply if you would like to explore this.

{signature}""",

    """{salutation} {name},

I am still happy to share a quick sketch or visual sample if it is helpful. Many of our clients use animation to break down services, explain strategy, or walk users through dashboards and pages.

If {company} has anything you are trying to simplify, I would love to help you explore it. Just reply if you want me to send something over.

You will find past examples in the signature below.

{signature}""",

    """{salutation} {name},

Thought I would check in one last time.

If you are still curious what an animated whiteboard explainer might look like for {company}, I would be glad to share something rough, a short teaser, or a script to get the ball rolling.

You can find our work in the link below. Reply anytime if you are interested.

{signature}""",

    """{salutation} {name},

Just reaching out again before I close this thread. If you think animated storytelling could be of value to {company}, I would love to put something together.

Even a 10-second sketch can be a useful way to explore what is possible.

Feel free to reply anytime.

{signature}""",

    """{salutation} {name},

If you are still considering creative ways to showcase what {company} does, animated storytelling could be a great tool to accelerate conversions.

I would be happy to send over a short visual teaser to get the ideas flowing.

No pressure, just a creative option to keep in mind. Reply anytime or take a peek at some of our previous work. The link is in my signature.

{signature}""",

    """{salutation} {name},

Circling back once more before I close the loop.

If there is anything at {company} you have been meaning to simplify, such as those quarterly reports your team never reads, whiteboard animation could help bring that to life.

I would be happy to draft something visual if you want to see what that might look like. You can reply anytime or check out some of our previous work on our website, linked in my signature.

{signature}""",

    """{salutation} {name},

Reaching out one last time before I close the loop. If you are still exploring creative ways to showcase what {company} offers, this could be a great fit.

I would be glad to put together a simple teaser or sketch if you are curious. Reply anytime or check out some of our past projects. The link is in my signature.

{signature}""",

    """{salutation} {name},

I hope your week is going well. I am wrapping up some projects and wanted to reach out again before I close things out.

If you would still like to explore using whiteboard videos to support {company}'s messaging, I would love to help. Simply reply or take a peek at some of our previous work on our website, which is linked in my signature.

{signature}""",

    """{salutation} {name},

A quick follow-up before I close out my list. If now is not the right time, no worries at all.

But if you are curious about how whiteboard animation might help {company}, I am still open to sharing a quick demo. No pressure. You can reply anytime or skim through some of our previous projects to see what we have done for other businesses. The link is in the signature.

{signature}""",

    """{salutation} {name},

Just one last follow-up in case you missed my previous notes. I would still be happy to sketch a teaser for {company} if you are curious to see what whiteboard animation can do.

It could help simplify one of your key offerings or assist with your latest project launch. If you are a little curious, just hit reply or check out some of our past work, which is already linked in my signature.

{signature}"""
]

def build_email(template, name, company, salutation, signature):
    return template.format(name=name, company=company, salutation=salutation, signature=signature)

def fetch_records():
    url = f"{API_BASE}/{NOCODB_PROJECT_ID}/{NOCODB_OUTREACH_TABLE_ID}/rows?user_field_names=true"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()["list"]

def update_record(record_id, payload):
    url = f"{API_BASE}/{NOCODB_PROJECT_ID}/{NOCODB_OUTREACH_TABLE_ID}/rows/{record_id}"
    r = requests.patch(url, headers=HEADERS, json=payload)
    r.raise_for_status()

def main():
    print("🚀 Generating Email 3 follow-ups...")
    records = fetch_records()
    eligible = []

    for record in records:
        name = record.get("name", "").strip()
        company = record.get("company name", "").strip()
        email3 = record.get("email 3", "").strip()
        record_id = record["id"]

        print(f"→ Checking {record_id}...")

        if name and company and not email3:
            eligible.append((record_id, name, company))
            print("   ✅ Eligible")
        else:
            print("   ❌ Skipping — missing name/company or email 3 already exists")

    if not eligible:
        print("⚠️ No eligible records found.")
        return

    random.shuffle(eligible)
    updated = 0

    for record_id, name, company in eligible:
        template = random.choice(TEMPLATES)
        salutation = random.choice(SALUTATIONS)
        signature = random.choice(SIGNATURES)
        content = build_email(template, name, company, salutation, signature)

        update_record(record_id, {"email 3": content})
        updated += 1
        print(f"✅ Email 3 written for {name}")

    print(f"\n🎯 Done. {updated} follow-ups generated.")

if __name__ == "__main__":
    main()
