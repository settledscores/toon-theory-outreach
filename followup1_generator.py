import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

# NocoDB setup
NOCODB_API_KEY = os.getenv("NOCODB_API_KEY")
NOCODB_PROJECT_ID = os.getenv("NOCODB_PROJECT_ID")
NOCODB_OUTREACH_TABLE_ID = os.getenv("NOCODB_OUTREACH_TABLE_ID")
NOCODB_BASE_URL = os.getenv("NOCODB_BASE_URL")
API_BASE = f"{NOCODB_BASE_URL}/v1/db/data"

SALUTATIONS = ["Hi there", "Hey there", "Hello there", "Hi", "Hey", "Hello"]

SIGNATURES = [
    "Warm regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent — Founder, Toon Theory\nwww.toontheory.com"
]

TEMPLATES = [
    """{salutation} {name},

Just looping back in case this got lost in your inbox. I mentioned how whiteboard animation could support {company}’s messaging ;  and I still believe there’s a great fit here.

These videos are especially helpful when you’re trying to explain something technical, strategic, or new in a way that sticks.

If it helps, I’d be happy to put together a short script or visual sample to show what this could look like.

Feel free to reply if you’d like to explore it. You’ll find examples of our work in my signature.

{signature}""",

    """{salutation} {name},

Wanted to follow up in case this timing works better for you. Whiteboard animation can be a surprisingly simple way to make your message clearer and more memorable ;  especially for B2B communication.

For {company}, this could mean faster understanding and stronger engagement, both internally and externally.

If you're open to a quick sketch or demo, I’d be happy to create one based on something you’re working on.

There’s a link to our past projects in my signature if you’d like to browse.

{signature}""",

    """{salutation} {name},

Just circling back. I realize it can be tricky to see how something like whiteboard animation fits into a business like {company}, which is why I’d love to show rather than tell.

If you’d be open to a 10-second visual sample or a short script tailored to your brand, I’d be glad to share one.

It’s no obligation, just a way to explore what this could look like in your context.

You’ll find some of our past work linked in my signature.

{signature}""",

    """{salutation} {name},

Following up briefly in case you’re still open to exploring how animated storytelling could help simplify {company}’s messaging.

It’s something that’s worked well for businesses trying to explain detailed services, product workflows, or thought leadership content in a more digestible way.

Happy to create a short, customized sample if you’d like a clearer sense of how this could look.

Reply anytime ;  there’s also a link to our previous work below.

{signature}""",

    """{salutation} {name},

I didn’t want to leave things hanging without checking in. I mentioned how whiteboard animation can be a strong complement to what {company} is already doing, especially when you’re communicating ideas that needs a touch of clarity or personality.

If it’s helpful, I can pull together a short visual sketch or sample script based on one of your key offerings.

No pressure ;  just a creative starting point for you to consider.

You’ll find some of our work linked in my signature.

{signature}""",

    """{salutation} {name},

Reaching out again in case the idea of using whiteboard animation is still on your radar.

It’s often a great fit for simplifying dense content, making internal updates more engaging, or creating educational pieces that feel more human.

For {company}, I’d be glad to sketch a quick visual or draft a short script so you can see what this might look like in practice.

Reply when you can, or check out some examples in the signature below.

{signature}""",

    """{salutation} {name},

Quick follow-up in case now’s a better time. Our last email was about how visual storytelling could help {company} make certain messages feel more clear and engaging.

If you're curious, I could create a ten-second teaser or a rough script so you can get a sense of what’s possible.

Just reply if you’d like to explore. There’s a link to some of our previous work in the signature below.

{signature}""",

    """{salutation} {name},

I wanted to briefly follow up to see if the idea of a quick, low-lift demo might interest you.

These kinds of animations are used to clarify big-picture strategies, improve training content, or explain services in a more human way.

If {company} has something complex or critical to explain, I’d love to put together a sample to show what it might look like.

Reply when ready, and check out some past examples linked below.

{signature}""",

    """{salutation} {name},

I know inboxes get full fast, so here's a quick follow up.

Whiteboard storytelling might be a surprisingly effective way for {company} to simplify something your audience or team needs to grasp quickly.

If you’re still open to it, I can send a short demo ;  a sample script or 10-second sketch ;  to give you a feel.

Let me know, or feel free to check out some of our past work in the signature.

{signature}""",

    """{salutation} {name},

Just checking in one more time.

I understand if now’s not ideal, but I still think there’s value in exploring how a short whiteboard video could help {company} communicate more clearly.

It could be a great fit for onboarding, product overviews, or thought leadership ;  and I’d be happy to show you a sample.

You can reply any time, or check out some of our past wor linked in my signature.

{signature}""",

    """{salutation} {name},

I wanted to circle back following my last email about using whiteboard animation at {company}. These videos can really simplify complex ideas and help you connect with your audience in a memorable way.

If you’re open to it, I’d love to put together that quick sketch or script I mentioned earlier — something tailored specifically to your key offerings or challenges.

Feel free to reply anytime. And just in case you missed it, some of our past projects are linked in my signature.

{signature}""",

    """{salutation} {name},

Just circling back as I didn’t want you to miss out on the chance to explore whiteboard animation for {company}.

Our animations are designed to help businesses like yours increase engagement, boost clarity, and convert more customers — all with story-driven visuals.

If you'd like, I can create a short demo or script as a no-pressure way to see how this could work for your team.

You’ll find examples of our work linked in my signature. Let me know if you’d like to see something specific.

{signature}""",

    """{salutation} {name},

Following up on my previous note about whiteboard animation at {company}.

Many of our clients find these videos help explain their offerings faster and more clearly, which often leads to more meaningful conversations and better results.

If it’s helpful, I’d be happy to draft a quick concept or short sample that fits your brand voice and messaging.

You can reply anytime, and our portfolio is linked below if you want to get a feel for what we do.

{signature}""",

    """{salutation} {name},

Hope you’re well. I wanted to check back in and remind you about the offer I shared — a quick, tailored script or visual teaser that could spark some ideas.

It’s a simple, no-strings way to explore how animation can support your {company}'s messaging and help your audience understand your value more clearly.

Feel free to reply if you want to see this, or browse some of our previous projects linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to reconnect after my last email about how {company} could benefit from whiteboard animation.

This type of video storytelling often boosts engagement and helps simplify complicated topics — making your message easier to remember.

If you’re curious, I’d be glad to draft a short teaser or script for you to review.

Please reply anytime, and there’s a link to our work in my signature if you want to take a look.

{signature}""",

    """{salutation} {name},

Reaching out again about the opportunity for {company} to stand out using whiteboard animation.

Whether it’s for pitching, explaining products, or internal training, these videos make complex ideas clearer and more engaging.

If you’re open to it, I can prepare a quick demo or script sample tailored to your brand — no pressure at all.

You’ll find examples of our previous work linked below. Let me know if you’d like to take a peek.

{signature}""",

    """{salutation} {name},

Following up to see if you’d be interested in exploring how animation could support {company}’s storytelling and messaging.

Our videos help businesses clarify key ideas quickly, often leading to better audience connection and increased conversions.

If you want, I can create a brief sketch or script demo tailored to your offerings, just to show what’s possible.

Please reply anytime, and you can also check out our portfolio linked in the signature.

{signature}""",

    """{salutation} {name},

Hope this finds you well. I’m following up on my previous email offering a quick, no-commitment demo to show how whiteboard animation might work for {company}.

These animations are a great way to explain services or products in an engaging, easy-to-understand format.

If you’d like me to put something together, just let me know. You’ll find some past examples linked below too.

{signature}""",

    """{salutation} {name},

Just reaching out again about the possibility of using whiteboard animation to enhance {company}’s messaging.

This approach often helps businesses increase engagement, simplify communication, and improve conversion rates.

If you’re curious, I’d be happy to draft a quick demo or script for you to review at your convenience.

You can reply any time, and there’s a link to our previous work in my signature.

{signature}""",

    """{salutation} {name},

Checking in one more time to see if you’d like to explore whiteboard animation for {company}.

We help clients bring their ideas to life through story-driven visuals that capture attention and make messages stick.

If you’d like, I can prepare a short sample or script tailored to your needs, no strings attached.

Please feel free to reply, and you can browse some of our past projects linked below.

{signature}"""
]

def fetch_records():
    url = f"{API_BASE}/{NOCODB_PROJECT_ID}/{NOCODB_OUTREACH_TABLE_ID}/rows"
    headers = {"Authorization": f"Bearer {NOCODB_API_KEY}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()["list"]

def update_record(record_id, content):
    url = f"{API_BASE}/{NOCODB_PROJECT_ID}/{NOCODB_OUTREACH_TABLE_ID}/rows/{record_id}"
    headers = {
        "Authorization": f"Bearer {NOCODB_API_KEY}",
        "Content-Type": "application/json"
    }
    r = requests.patch(url, headers=headers, json={"email 2": content})
    r.raise_for_status()

def generate_followup_email(fields, template, salutation, signature):
    return template.format(
        name=fields.get("name", "[name]").strip(),
        company=fields.get("company name", "[company]").strip(),
        salutation=salutation,
        signature=signature
    )

def main():
    print("🔍 Generating Follow-up 2 emails...")
    records = fetch_records()
    updated = 0

    for record in records:
        if not record.get("name") or not record.get("company name"):
            print("   Skipping — missing name or company.\n")
            continue
        if record.get("email 2", "").strip():
            print("   Skipping — email 2 already exists.\n")
            continue

        template = random.choice(TEMPLATES)
        salutation = random.choice(SALUTATIONS)
        signature = random.choice(SIGNATURES)
        content = generate_followup_email(record, template, salutation, signature)

        update_record(record["id"], content)
        updated += 1
        print(f"✅ Email 2 written for: {record['name']}\n")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
