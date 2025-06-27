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

Hope your week’s going well. Just wanted to follow up on the note I sent a few days ago about Toon Theory.

I still think there’s potential to try out animated storytelling with one of your core offerings.

I’d still be more than happy to draft a script or sketch a ten-second demo to show what kind of potential this could have.

Feel free to reply if you're still curious to explore the fit. There’s a link to our site in my signature if you’d like to check out some of our past work.

{signature}""",
    """{salutation} {name},

I figured I’d follow up on my previous note just in case it got buried.

I mentioned that we create animated explainers to help companies like yours simplify their messaging and stand out.

If you're open to it, I’d be happy to sketch a quick teaser or draft a sample script. Just a creative way to see what this could look like in action.

Feel free to reply if that sounds interesting. There's also a link to our site in my signature if you’d like to see some of our past work.

{signature}""",
    """{salutation} {name},

Just circling back in case this is still something worth exploring.

Animation can be a powerful way to bring clarity to complex ideas — we’ve seen it work well in a range of industries.

If you’d like to test the waters, I’d be glad to share a short sample tailored to your brand.

Feel free to reply any time. You’ll find a link to our past work in my signature.

{signature}""",
    """{salutation} {name},

Just wanted to check in again — we create whiteboard animations that help explain and differentiate brands more clearly.

Happy to sketch out a quick visual draft if you’re interested in seeing what it might look like for your team.

You’ll find a few past examples on our site (link in my signature). No pressure at all.

{signature}""",
    """{salutation} {name},

Hope you're doing well. I know inboxes fill up fast, so thought I'd try again.

If there's a message you're trying to simplify or a service you're trying to highlight, animation might be worth a look.

Let me know if you'd be open to seeing a visual draft or sample storyboard.

{signature}""",
    """{salutation} {name},

Just a quick nudge in case my last message got buried.

If you’re still exploring ways to communicate more clearly or creatively, I’d be happy to sketch a short explainer to show how this might work for your brand.

You’ll find a few samples in the link in my signature.

{signature}""",
    """{salutation} {name},

Hope your week’s going well.

I wanted to quickly follow up to see if you’re still exploring ways to make your messaging more engaging.

I’d be happy to sketch something short to help visualize what that might look like.

Let me know what you think.

{signature}""",
    """{salutation} {name},

Just following up in case this is still on your radar.

Animation’s helped a lot of our clients explain complex services and ideas in a simpler, more memorable way.

Would you be open to seeing a quick visual mockup?

{signature}""",
    """{salutation} {name},

I wanted to follow up on the note I sent recently about Toon Theory.

We help teams cut through the noise using short, story-driven animations. It could be a good fit if you’re looking for a new way to explain what you do.

Happy to draft something simple if you'd like.

{signature}""",
    """{salutation} {name},

I know you’re probably swamped, but I thought I’d reach out again.

Animation has been really useful for clients looking to simplify their message and get noticed.

Let me know if you'd like a rough idea of what that could look like for your brand.

{signature}""",
    """{salutation} {name},

Just revisiting my earlier message. If now’s a better time to explore this, I’d love to reconnect.

We focus on creating short, compelling whiteboard animations that help companies express themselves better.

Happy to share a quick draft if that’s helpful.

{signature}""",
    """{salutation} {name},

I wanted to give this one more shot in case it’s still a conversation worth having.

Animation might be a smart way to simplify something you’re already doing — whether it’s internal messaging or customer-facing content.

Let me know if you're interested.

{signature}""",
    """{salutation} {name},

Reaching out again to see if this might still be relevant.

If you’re curious what animation might look like for your message, I’d be glad to share a quick visual or sketch to start.

Just hit reply if you're open to it.

{signature}""",
    """{salutation} {name},

Circling back to see if a short animation might be something you’d like to explore.

Even a quick 10-second sketch can give you a sense of how it all works — especially for explaining services or onboarding processes.

Let me know if you’d like to see a mockup.

{signature}""",
    """{salutation} {name},

Following up once more — we help brands explain themselves in a clear and engaging way using short, custom animations.

If you’re interested in seeing what that might look like, just let me know.

There’s a peek at past projects in my signature.

{signature}"""
]
    """{salutation} {name},

I just wanted to check in again and see if the idea of using whiteboard animation for {company} has sparked any interest. Animation can be a great way to highlight key messages and bring stories to life in a memorable way.

If you'd like, I can put together a simple draft or a short sample video to show how this could work for you.

You can also find examples of our previous work linked in my signature. Please don’t hesitate to reply if you want to explore this.

{signature}""",

    """{salutation} {name},

Following up once more because I think animation could really help {company} communicate ideas in a clear and compelling way. Many of our clients have seen great results from adding this creative approach to their messaging.

I’d be happy to sketch out a quick teaser or script tailored to your brand.

Feel free to reply if you’d like to see what this might look like. You’ll find links to our past projects in my signature.

{signature}""",

    """{salutation} {name},

I hope this note finds you well. I’m reaching out again to offer a creative way for {company} to stand out using animated whiteboard videos.

Even a short, simple animation can make complex ideas easier to understand and more engaging for your audience.

If that sounds interesting, I’d be glad to prepare a brief demo or script to share with you.

Please reply anytime. Past examples are linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to check in and see if you have any questions or thoughts about using whiteboard animation at {company}.

It’s a creative way to explain what you do, and it can really help with marketing, training, or internal communications.

If you’d like, I can send over a quick sample tailored to your needs.

You’ll find some of our past work in my signature. I’m here if you want to chat.

{signature}""",

    """{salutation} {name},

Checking in again to share how whiteboard animation could help {company} communicate clearly and creatively with your audience.

Animation can make even the most complicated topics accessible and interesting, which often leads to better engagement and increased trust.

If you’re open to it, I’d love to draft a short teaser for you to review.

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

It’s an engaging way to capture attention and explain what makes your key offerings unique.

If it sounds useful, I’d be glad to prepare a quick visual sample or script to show you what’s possible.

You can reply anytime, and links to our past work are in the signature.

{signature}""",

    """{salutation} {name},

I’m checking in one more time about the opportunity to use whiteboard animation at {company}.

Many businesses find that even short animations help clarify their message and make their content more memorable.

If you’d like, I can put together a brief teaser to help you explore this option.

Please feel free to reply at any time. Examples of our work are linked in my signature.

{signature}""",

    """{salutation} {name},

Just wanted to follow up to see if you’ve had a chance to consider whiteboard animation for {company}.

It’s a creative way to bring your ideas to life and connect with your audience more effectively.

If you’re interested, I’d be happy to share a quick demo or script tailored to your needs.

You’ll find past examples linked in my signature. Reply whenever you’re ready.

{signature}""",

    """{salutation} {name},

I wanted to check in again to offer support if you’re thinking about how {company} could benefit from whiteboard animation.

We’ve helped many businesses explain their offerings clearly and creatively through short, engaging videos.

If you’d like, I can draft a quick sample to show how this might work for you.

Please don’t hesitate to reply. Our past projects are linked below.

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
