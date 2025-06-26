import os
import random
import re
from airtable import Airtable
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
airtable = Airtable(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME, AIRTABLE_API_KEY)

# --- Variant Lists ---

subject_variants = [
    "Let’s make your message stick",
    "A quick thought for your next project",
    "Helping your ideas stick visually",
    "Turn complex into simple (in 90 seconds)",
    "Your story deserves to be told differently",
    "How about a different approach to your messaging?",
    "Making your story unforgettable",
    "Visual storytelling for busy decision-makers",
    "Helping messages land better for businesses like {company}",
    "For when words aren’t enough, {name},"
]

paragraph1_templates = [
    "Hi {name}, I came across {company} recently and wanted to reach out directly.",
    "Hello {name}, Just saw {company} and thought you might be the right person to speak with.",
    "Hey {name}, I came across {company} recently and thought I’d drop you a quick note.",
    "Hi {name}, Stumbled on {company} the other day and wanted to get in touch.",
    "Hi {name}, Stumbled across {company} and thought I’d reach out.",
    "Hi {name}, Just spotted {company} and thought there could be an opportunity to collaborate.",
    "Hi {name}, Hope you don't mind me reaching out; I came across {company} recently and thought we could collaborate."
]

paragraph2_variants = [
    "I'm Trent. I run Toon Theory, a whiteboard animation studio based in the UK. We create strategic, story-driven explainer videos that simplify complex ideas and boost engagement, especially for B2B services, thought leadership, and data-driven education.",
    "I'm Trent, founder of Toon Theory – a UK-based animation studio that creates story-driven whiteboard animations to help businesses like yours explain ideas with clarity and speed.",
    "I'm Trent, I lead a creative studio called Toon Theory. We work with businesses like yours to turn abstract nonsense into short, powerful videos that actually stick.",
    "I'm Trent, I run Toon Theory, an animation studio based in the UK. We focus on helping businesses cut through the noise using clean, hand-drawn storytelling."
]

paragraph3_additional_variants = [
    "For {company}, I think there’s real potential to add a layer of visual storytelling that helps even more people 'get it' faster. Our animations are fully done-for-you: illustrations, scripting, voiceover, storyboard; and are often used by folks like you for:",
    "There’s a lot of potential for {company} to benefit from visual storytelling — it often helps others understand what you do much faster. We handle everything end-to-end: scripting, voiceover, design and animation. Folks like you often use it for:"
]

paragraph4b_variants = [
    "These videos often help businesses increase engagement by up to 60%, double conversion rates, and boost message retention by up to 80%.",
    "Our clients often see up to 2x engagement and 80% stronger retention when they present ideas visually.",
    "These animations don’t just explain, they convert; often doubling engagement, boosting sales and improving trust.",
    "By turning ideas into clear visuals, our animations consistently drive higher conversions, stronger engagement, and longer message recall.",
    "We've seen teams cut through noise, capture attention faster, and turn interest into action — all by using the power of animated storytelling."
]

paragraph5_variants = [
    "If you'd be open to it, I’d love to share a brief demo tailored to one of your core offerings. This could be a sample script or a ten second sketch. All at zero cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.",
    "If you’re open to it, I’d love to share a quick sketch or sample script tailored to one of your key offerings at zero cost to you. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.",
    "I'd be happy to draft a no-cost, ten-second demo around something core to your brand. Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it.",
    "Would you be open to seeing a quick script or ten-second sketch built with {company} in mind? Absolutely no pressure, just keen to see what this could look like with {company}'s voice behind it."
]

paragraph6_variants = [
    "Thanks for putting something refreshing out there.",
    "Thanks for leading with both heart and strategy.",
    "Keep doing what you do, it's making an impact."
]

paragraph7_cta_variants = [
    "Feel free to reply if you’d like to explore what this could look like. There’s also a link to our site in my signature if you’d like to take a peek at some of our previous work.",
    "You’ll find a link to our site in the signature if you’d like to check out our past work — and I’d love to hear your thoughts if it sparks anything.",
    "Reply any time if it feels like a fit. There’s a link in the signature if you’re curious to see what we’ve done for others.",
    "If you're open to chatting further? Just hit reply — and there’s a site link in the signature if you’d like to see a handful of our past projects."
]

signature_variants = [
    "Warm regards,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "All the best,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Cheers,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Take care,\nTrent — Founder, Toon Theory\nwww.toontheory.com",
    "Sincerely,\nTrent — Founder, Toon Theory\nwww.toontheory.com"
]

def parse_use_cases(use_case_field):
    raw = str(use_case_field or "")
    return [u.strip() for u in raw.split("|") if u.strip()]

def build_email(fields):
    name = fields.get("name") or "there"
    company = fields.get("company name") or "your company"
    use_cases = parse_use_cases(fields.get("use case"))[:3]

    email = f"""
{random.choice(subject_variants).format(name=name, company=company)}

{random.choice(paragraph1_templates).format(name=name, company=company)}

{random.choice(paragraph2_variants)}

{random.choice(paragraph3_additional_variants).format(company=company)}
- {use_cases[0] if len(use_cases) > 0 else ''}
- {use_cases[1] if len(use_cases) > 1 else ''}
- {use_cases[2] if len(use_cases) > 2 else ''}

{random.choice(paragraph4b_variants)}

{random.choice(paragraph5_variants).format(company=company)}

{random.choice(paragraph6_variants)}

{random.choice(paragraph7_cta_variants)}

{random.choice(signature_variants)}
""".strip()

    return email

def update_email_field(record_id, content):
    airtable.update(record_id, {"email 1": content})

def main():
    records = airtable.get_all()
    updated = 0

    for record in records:
        fields = record.get("fields", {})
        record_id = record["id"]
        if not fields.get("email 1"):
            email_body = build_email(fields)
            update_email_field(record_id, email_body)
            updated += 1
            print(f"✅ Email written for {record_id}")

    print(f"\n🎯 Done. {updated} records updated.")

if __name__ == "__main__":
    main()
