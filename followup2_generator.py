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

{signature}""",

        """{salutation} {name},

I just wanted to check in again and see if the idea of using whiteboard animation for {company} has sparked any interest. Animation can be a great way to highlight key messages and bring stories to life in a memorable way.

If you'd like, I can put together a simple draft or a short sample video to show how this could work for you.

You can also find examples of our previous work linked in my signature. Please don’t hesitate to reply if you want to explore this.

{signature}""",

    """{salutation} {name},

Following up once more because I think animation could really help {company} communicate ideas in a clear and compelling way. Many of our clients have seen great results from adding this creative approach to their messaging.

I’d be happy to sketch out a quick visual or script that suits your brand and goals.

Feel free to reply if you’d like to see what this might look like. You’ll find links to our past projects in my signature.

{signature}""",

    """{salutation} {name},

I hope this note finds you well. I’m reaching out again to offer a creative way for {company} to stand out using animated whiteboard videos.

Even a short, simple animation can make complex ideas easier to understand and more engaging for your audience.

If that sounds interesting, I’d be glad to prepare a brief demo or script to share with you.

Please reply anytime. Past examples are linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to reconnect in case my previous notes got buried. If you have any questions or thoughts about using whiteboard animation at {company}, I'd be more than happy to answer them..

It’s a creative way to explain what you do, and it can really help with marketing, training, or internal communications.

If you’d like, I can send over a quick teaser or script sample.

You’ll find some of our past work in my signature. I’m here if you want to chat.

{signature}""",

    """{salutation} {name},

Checking in again to share how whiteboard animation could help {company} communicate clearly and creatively with your audience.

Animation can make even the most complicated topics accessible and interesting, which often leads to better engagement.

If you’re open to it, I’d love to draft a short visual concept for you to review.

Feel free to reply anytime, and you can see examples of our work linked below.

{signature}""",

    """{salutation} {name},

I wanted to reach out once more to highlight the potential benefits of whiteboard animation for {company}.

Whether it’s for sales, marketing, onboarding, or internal messaging, animation can be a great tool to simplify ideas and keep people interested.

If you’re curious, I’d be happy to create a short sample or script that fits your goals.

Please reply whenever you’re ready. Past projects are linked in my signature.

{signature}""",

    """{salutation} {name},

Just following up again because I think animation could add real value to {company}’s messaging.

It’s an engaging way to capture attention and explain what makes your business unique.

If it sounds useful, I’d be glad to prepare a quick visual sample or script to show you what’s possible.

You can reply anytime, and links to our past work are in the signature.

{signature}""",

    """{salutation} {name},

I’m checking in one last time about the opportunity to use whiteboard animation at {company}.

Many teams find that even short animations help clarify their message and make their content more memorable.

If you’d like, I can put together a brief draft to help you explore this option.

Please feel free to reply at any time. Examples of our work are linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to follow up to see if you’ve had a chance to consider adopting whiteboard animation to supercharge {company}'s messaging.

It’s a creative way to bring your ideas to life and connect with your audience more effectively.

If you’re interested, I’d be happy to share a quick demo or script tailored to your needs.

You’ll find past examples linked in my signature. Reply whenever you’re ready.

{signature}""",

    """{salutation} {name},

I wanted to check in one last time to offer support if you’re thinking about how {company} could benefit from whiteboard animation.

We’ve helped many businesses explain their offerings clearly and creatively through short, engaging videos.

If you’d like, I can draft a quick sample to show how this might work for you.

Please don’t hesitate to reply. Our past projects are linked below.

{signature}""",
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
